#!/usr/bin/env python3
"""Plan an opt-in workspace copy without accessing the application's database."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

EXCLUDED_TREES = (
    'backend/storage/app/private/invoice-temp',
    'backend/storage/framework/cache/data',
    'backend/storage/framework/sessions',
    'backend/storage/framework/views',
    'frontend/dist',
)
OCR_KEYS = ('OCR_TESSERACT', 'OCR_PDFTOPPM', 'OCR_PDFINFO', 'OCR_PYTHON', 'OCR_LOCK_PATH')
NATIVE_FILESYSTEMS = ('ext4', 'xfs', 'btrfs', 'overlay')
COPY_WORKERS = 8


class CopyError(Exception):
    pass


def excluded(relative: str) -> bool:
    return (any(relative == tree or relative.startswith(tree + '/') for tree in EXCLUDED_TREES)
            or (relative.startswith('backend/bootstrap/cache/') and relative.endswith('.php'))
            or (relative.startswith('backend/storage/framework/testing/'))
            or relative == 'backend/storage/app/private/invoice-ocr.lock')


def inventory(source: Path, links: list[str] | None = None) -> tuple[list[str], list[str]]:
    files, directories = [], []
    pending = [source]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(source).as_posix()
                if excluded(relative):
                    continue
                if entry.is_symlink():
                    files.append(relative)
                    if links is not None:
                        links.append(relative)
                elif entry.is_dir(follow_symlinks=False):
                    directories.append(relative)
                    pending.append(path)
                else:
                    files.append(relative)
    return sorted(files), sorted(directories)


def fingerprint(path: Path) -> str:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return 'link:' + os.readlink(path)
    if not stat.S_ISREG(mode):
        raise CopyError('A origem contém um arquivo especial; revise antes de copiar.')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def remap_ocr(contents: bytes, source: Path, destination: Path) -> tuple[bytes, list[str]]:
    changed = []
    lines = contents.decode('utf-8', errors='surrogateescape').splitlines(keepends=True)
    pattern = re.compile(r'^(\s*(?:export\s+)?(' + '|'.join(OCR_KEYS) + r')\s*=\s*)([\'\"]?)' + r'(?i:(' + re.escape(str(source)) + r'))(?=/)')
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            try:
                same_directory = Path(match[4]).samefile(source)
            except OSError:
                same_directory = False
            if same_directory:
                lines[index] = line[:match.start(4)] + str(destination) + line[match.end():]
                changed.append(match[2])
    return ''.join(lines).encode('utf-8', errors='surrogateescape'), changed


def prepare(source: Path, destination: Path) -> tuple[dict, list[str], list[str]]:
    if destination.exists() or destination.is_symlink():
        raise CopyError('O destino já existe; escolha uma pasta nova. Nada foi sobrescrito.')
    if source == destination or source in destination.parents or destination in source.parents:
        raise CopyError('Origem e destino não podem conter um ao outro.')
    for required in ['docs/PROJECT_SPEC.md', 'backend/artisan', 'frontend/package.json', 'docker-compose.yml']:
        if not (source / required).is_file():
            raise CopyError('A origem não contém a estrutura esperada do EcoWatt.')
    if not (source / '.git').is_dir() or (source / '.git').is_symlink():
        raise CopyError('Este roteiro exige um clone com .git próprio; worktrees precisam de revisão separada.')
    ancestor = destination.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    filesystem = subprocess.run(['findmnt', '-T', str(ancestor), '-n', '-o', 'FSTYPE'],
                                check=True, capture_output=True, text=True).stdout.strip()
    if filesystem not in NATIVE_FILESYSTEMS:
        raise CopyError('O destino precisa estar em um sistema de arquivos Linux local suportado.')
    links = []
    files, directories = inventory(source, links)
    external_links = sum(not (source / file).resolve().is_relative_to(source) for file in links)
    locks = sum(file.startswith('.git/') and file.endswith('.lock') for file in files)
    temporary = source / 'backend/storage/app/private/invoice-temp'
    pending_originals = temporary.exists() and any(path.is_file() and path.name != '.gitignore' for path in temporary.rglob('*'))
    linked_configuration = any((source / file).is_symlink() for file in ['.env', 'backend/.env'])
    ocr_changes = []
    if (source / 'backend/.env').is_file():
        _, ocr_changes = remap_ocr((source / 'backend/.env').read_bytes(), source, destination)
    plan = {
        'mode': 'plan', 'files': len(files), 'directories': len(directories),
        'destination_filesystem': filesystem, 'external_links': external_links,
        'git_locks': locks, 'pending_originals': bool(pending_originals),
        'linked_configuration': linked_configuration,
        'ocr_keys_to_remap': ocr_changes,
        'copy_ready': not external_links and not locks and not pending_originals and not linked_configuration,
        'database_action': 'none', 'source_action': 'read_only',
    }
    return plan, files, directories


def copy_workspace(source: Path, destination: Path, plan: dict, files: list[str], directories: list[str]) -> dict:
    if not plan['copy_ready']:
        raise CopyError('Há links externos/configurações vinculadas, locks do Git ou originais pendentes; resolva antes da cópia.')
    if not destination.parent.is_dir():
        raise CopyError('Crie o diretório pai escolhido antes da cópia.')
    def copy_file(file: str) -> list[str]:
        original, copied = source / file, destination / file
        remapped = []
        if original.is_symlink():
            target = os.readlink(original)
            if os.path.isabs(target):
                target = str(destination / original.resolve().relative_to(source))
            copied.symlink_to(target)
        else:
            shutil.copy2(original, copied)
            if original.name == '.env' or original.name.startswith('.env.'):
                copied.chmod(0o600)
            if file == 'backend/.env':
                contents, remapped = remap_ocr(copied.read_bytes(), source, destination)
                copied.write_bytes(contents)
        return remapped

    def verify_file(file: str) -> None:
        original, copied = source / file, destination / file
        if fingerprint(original) != before[file]:
            raise CopyError('A origem mudou durante a cópia; a cópia não foi validada.')
        if original.is_symlink():
            expected = original.resolve().relative_to(source)
            if copied.resolve() != destination / expected:
                raise CopyError('Um link da cópia não passou pela verificação.')
        elif file == 'backend/.env':
            expected, _ = remap_ocr(original.read_bytes(), source, destination)
            if copied.read_bytes() != expected:
                raise CopyError('A configuração copiada não passou pela verificação.')
        elif fingerprint(copied) != before[file]:
            raise CopyError('Um arquivo copiado não passou pela verificação.')

    with ThreadPoolExecutor(max_workers=COPY_WORKERS) as executor:
        before = dict(zip(files, executor.map(lambda file: fingerprint(source / file), files)))
        destination.mkdir(mode=0o700)
        try:
            for directory in directories:
                (destination / directory).mkdir(mode=0o700)
            remapped = []
            for keys in executor.map(copy_file, files):
                remapped.extend(keys)
            # Laravel resolves the views directory during bootstrap, before it can recreate it.
            for relative in EXCLUDED_TREES:
                if relative.startswith('backend/'):
                    current = destination
                    for part in Path(relative).parts:
                        current /= part
                        current.mkdir(mode=0o700, exist_ok=True)
            if inventory(source) != (files, directories):
                raise CopyError('A lista de arquivos da origem mudou durante a cópia; a cópia não foi validada.')
            list(executor.map(verify_file, files))
            return plan | {'mode': 'copied', 'verified': True, 'ocr_keys_remapped': remapped,
                           'copy_workers': COPY_WORKERS, 'runtime_directories_prepared': True,
                           'application_validation': 'pending', 'performance_comparison': 'pending'}
        except Exception:
            # Keep an incomplete destination for inspection; never erase the source or overwrite a retry.
            raise CopyError('A cópia ficou incompleta e foi mantida para revisão. A origem foi preservada.') from None


def main() -> int:
    parser = argparse.ArgumentParser(description='Planejar cópia do EcoWatt para Linux; sem alterações por padrão.')
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--copy', action='store_true', help='Executar a cópia explicitamente, sem iniciar serviços.')
    parser.add_argument('--source-paused', action='store_true', help='Confirmar que API, worker e editor não escrevem na origem.')
    arguments = parser.parse_args()
    try:
        requested_destination = arguments.destination.expanduser()
        if not requested_destination.is_absolute() or requested_destination.is_symlink():
            raise CopyError('Informe um destino absoluto novo, sem link simbólico.')
        source, destination = arguments.source.resolve(), requested_destination.resolve()
        plan, files, directories = prepare(source, destination)
        if arguments.copy:
            if not arguments.source_paused:
                raise CopyError('Pause as gravações na origem e confirme com --source-paused antes da cópia.')
            plan = copy_workspace(source, destination, plan, files, directories)
        print(json.dumps(plan, ensure_ascii=False))
        return 0
    except CopyError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print('Não foi possível preparar ou verificar a cópia. Confira os pré-requisitos e use um destino novo.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
