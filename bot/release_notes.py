import re
from aiogram import types
from utils.logger import logger

async def release(message: types.Message):
    '''отображение пунктов из указанного или последнего релиза'''
    try:
        # открываем и читаем файл README.md
        with open("README.md", "r", encoding="utf-8") as file:
            lines = file.readlines()

        # находим раздел "## Релизы"
        releases_start = None
        for idx, line in enumerate(lines):
            if line.strip() == "## Релизы":
                releases_start = idx
                break

        if releases_start is None:
            logger.error("The 'Releases' section was not found in README.md.")
            return

        # извлекаем номер версии из команды
        command_parts = message.text.split(maxsplit=1)
        version_pattern = re.compile(r"v?\.?(\d+)\.?(\d+)?\.?(\d+)?")

        target_version = None
        if len(command_parts) > 1:
            match = version_pattern.search(command_parts[1])
            if match:
                major = match.group(1)
                minor = match.group(2) if match.group(2) else "0"
                patch = match.group(3) if match.group(3) else "0"
                target_version = f"{major}.{minor}.{patch}"
        
        # Извлекаем релизные заметки
        release_notes = []
        inside_release = False
        version_found = False

        for line in lines[releases_start + 1:]:
            if line.startswith("### v."):
                current_version = line.strip().split()[1]
                if inside_release:
                    break  # останавливаемся после первого релиза

                if target_version:
                    if current_version == f"v.{target_version}":
                        version_found = True
                        inside_release = True
                        release_notes.append(line.strip())
                else:
                    inside_release = True
                    release_notes.append(line.strip())
            elif inside_release and line.strip():
                release_notes.append(line.strip())
            elif inside_release and not line.strip():
                break  # прерываем, когда встречаем первую пустую строку после релиза

        if release_notes:
            release_notes[0] = f"<b>{release_notes[0].replace('### ', '')}</b>"
            await message.reply("\n".join(release_notes), parse_mode="HTML")
        else:
            if target_version:
                logger.error(f"Release version {target_version} was not found in README.md.")
            else:
                logger.error("Failed to find the latest release information in README.md.")
    except FileNotFoundError:
        logger.error("README.md file not found.")
    except Exception as e:
        logger.error(f"An error occurred while reading the release: {e}")