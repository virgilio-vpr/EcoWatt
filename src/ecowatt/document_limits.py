"""Orçamento prévio de rasterização; não é sandbox nem habilita documentos.

Preparação para um adaptador isolado futuro. Dimensões devem vir do renderer,
não do cliente. Reserva antes de alocar; falhas/retries também consomem quota.
"""
from dataclasses import dataclass


class RasterLimitError(ValueError):
    """Código técnico fechado, sem conteúdo ou diagnóstico da biblioteca."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class RasterPolicy:
    """Tetos conservadores de preparação, ainda sem benchmark PDF/OCR."""

    max_side: int = 10_000
    max_page_pixels: int = 20_000_000
    max_document_pixels: int = 60_000_000
    max_document_bytes: int = 240_000_000
    max_renders: int = 32

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in (
                self.max_side, self.max_page_pixels, self.max_document_pixels,
                self.max_document_bytes, self.max_renders)):
            raise RasterLimitError("invalid_raster_policy")


@dataclass(frozen=True)
class RasterAllocation:
    page: int
    width: int
    height: int
    channels: int
    stride: int

    @property
    def pixels(self):
        return self.width * self.height

    @property
    def byte_count(self):
        return self.stride * self.height

    def verify(self, *, width: int, height: int, channels: int, stride: int,
               buffer: bytes | bytearray | memoryview):
        """Confere retorno sem copiar bytes; chamar antes de entregar ao OCR.

        Checagem posterior não evita alocação excessiva por renderer defeituoso.
        O futuro processo continua exigindo quota física de RAM pelo SO.
        """
        actual = (width, height, channels, stride)
        if (any(type(value) is not int for value in actual)
                or actual != (self.width, self.height, self.channels, self.stride)
                or not isinstance(buffer, (bytes, bytearray, memoryview))):
            raise RasterLimitError("raster_output_mismatch")
        try:
            with memoryview(buffer) as view:
                valid = view.c_contiguous and view.nbytes == self.byte_count
        except ValueError:
            valid = False
        if not valid:
            raise RasterLimitError("raster_output_mismatch")


class RasterBudget:
    """Uma instância por documento, uso sequencial no processo isolado futuro.

    Não reiniciar entre páginas, regiões, mudança de DPI, falhas ou retries.
    Contadores medem trabalho reservado, não RAM residente nem cópias do OCR.
    """

    def __init__(self, page_count: int, policy: RasterPolicy | None = None):
        if type(page_count) is not int or not 1 <= page_count <= 10:
            raise RasterLimitError("invalid_page_count")
        self._page_count = page_count
        self._policy = policy if policy is not None else RasterPolicy()
        self._pages = [0] * page_count
        self._pixels = self._bytes = self._renders = 0

    @property
    def usage(self):
        return {"pixels": self._pixels, "bytes": self._bytes, "renders": self._renders}

    def reserve(self, *, page: int, width: int, height: int, channels: int = 3,
                stride: int | None = None) -> RasterAllocation:
        """Dimensões finais em pixels, após escala/UserUnit/rotação/recorte.

        Inclui padding por linha; apenas amostras de oito bits, gray/RGB/RGBA.
        Cada região/repetição conta integralmente, mesmo na mesma página.
        """
        if (any(type(value) is not int for value in (page, width, height, channels))
                or not 1 <= page <= self._page_count or width <= 0 or height <= 0
                or channels not in (1, 3, 4)):
            raise RasterLimitError("invalid_raster_request")
        policy = self._policy
        if width > policy.max_side or height > policy.max_side:
            raise RasterLimitError("raster_side_limit")
        row_bytes = width * channels
        stride = row_bytes if stride is None else stride
        if type(stride) is not int or stride < row_bytes:
            raise RasterLimitError("invalid_raster_request")
        allocation = RasterAllocation(page, width, height, channels, stride)
        if self._pages[page - 1] + allocation.pixels > policy.max_page_pixels:
            raise RasterLimitError("raster_page_pixel_limit")
        if self._pixels + allocation.pixels > policy.max_document_pixels:
            raise RasterLimitError("raster_document_pixel_limit")
        if self._bytes + allocation.byte_count > policy.max_document_bytes:
            raise RasterLimitError("raster_document_byte_limit")
        if self._renders + 1 > policy.max_renders:
            raise RasterLimitError("raster_render_limit")
        self._pages[page - 1] += allocation.pixels
        self._pixels += allocation.pixels
        self._bytes += allocation.byte_count
        self._renders += 1
        return allocation
