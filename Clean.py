import collections
import shutil
import sys
from datetime import datetime
from pathlib import Path
from threading import Thread, RLock
from logger import get_logger

lock = RLock()

logger = get_logger(__name__)

# створюємо словник, згідно з яким визначаємо правила сортування файлів
# ключі - це тека(Folder), а значення - це список розширень файлів, які потрібно в цю теку(Folder) перемістити.
suffix_dict = {
    "Images": [".jpg", ".jpeg", ".png", ".svg"],
    "Documents": [".txt", ".docx", ".doc", ".pdf", ".xlsx", ".pptx"],
    "Archives": [".zip", ".gz", ".tar"],
    "Audio": [".mp3", ".ogg", ".wav", ".amr"],
    "Video": [".avi", ".mp4", ".mov", ".mkv"],
    "other": [],
}
# Створюємо функціонал для транслітерації назв на латинські та безпечні символи:
CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = (
    "a",
    "b",
    "v",
    "g",
    "d",
    "e",
    "e",
    "j",
    "z",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "r",
    "s",
    "t",
    "u",
    "f",
    "h",
    "ts",
    "ch",
    "sh",
    "sch",
    "",
    "y",
    "",
    "e",
    "yu",
    "ya",
    "je",
    "i",
    "ji",
    "g",
)

TRANS = {}
for cyrillic, latyn in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(cyrillic)] = latyn
    TRANS[ord(cyrillic.upper())] = latyn.upper()

# замінюємо кириличні символи на латинські


def normalize(name):
    global TRANS
    logger.info(f"File name '{name}' was normalized")
    return name.translate(TRANS)


# розпакування архівів


def unpack(archive_path, path_to_unpack):
    return shutil.unpack_archive(archive_path, path_to_unpack)


# Функція перевіряє, чи вже існує 'file' з такою назвою
# Якщо існує, то доповнюємо до назви в круглих дужках 3 різних символи


def is_file_exists(file, go_dir):
    if file in go_dir.iterdir():
        add_name = datetime.now().strftime("%d_%m_%Y_%H_%M_%S_%f")
        name = file.resolve().stem + f"({add_name})" + file.suffix
        file_path = Path(go_dir, name)
        logger.info(
            f"File with name '{file.resolve().stem}' is already exists and was renamed to {name}"
        )
        return file_path
    return file


# Перевіряємо чи існує необхідні теки, якщо немає - створюємо
# file - посилання, на файл який переміщуємо; go_dir - посилання, на теку, куди необхідно перемістити файл


def is_fold_exists(file, go_dir):
    if go_dir.exists():
        Thread(target=folder_sort, args=(lock, file, go_dir)).start()
    else:
        Path(go_dir).mkdir()
        logger.info(f"Folder with name '{go_dir}' was not exist and was created")
        Thread(target=folder_sort, args=(lock, file, go_dir)).start()


# замінює назву файла та переміщає в необхідну теку
# file - посилання, на файл який переміщаємо
# go_dir - посилання, на теку, куди необхідно перемістити файл


def folder_sort(file, go_dir):
    latin_name = normalize(file.name)  # перекладаємо назву на латиницю
    new_file = Path(go_dir, latin_name)  # створюємо шлях до файла з новою назвою
    file_path = is_file_exists(
        new_file, go_dir
    )  # перевіряємо чи вже існує файл з такою назвою
    file.replace(file_path)  # переміщуємо файл
    logger.info(f"File with name '{file.name}' was removed to {go_dir}")


def show_sort(param):
    total_dict = collections.defaultdict(list)
    files_dict = collections.defaultdict(list)

    for item in param.iterdir():
        if item.is_dir():
            for file in item.iterdir():
                if file.is_file():
                    total_dict[item.name].append(file.suffix)
                    files_dict[item.name].append(file.name)
    for k, v in files_dict.items():
        print()
        print(f" Folder '{k}' contains files: ")
        print(f" ---- {v}")

    print()
    print(
        "======================= File sorting completed successfully!!! ======================="
    )
    print()
    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        "| {:^15} | {:^17} | {:^43} |".format(
            "Folder name", "Number of files", "File extensions"
        )
    )
    print(
        "-------------------------------------------------------------------------------------"
    )

    for key, value in total_dict.items():
        k, a, b = key, len(value), ", ".join(set(value))
        print("| {:<15} | {:^17} | {:<43} |".format(k, a, b))

    print(
        "-------------------------------------------------------------------------------------"
    )
    print()


# Перевіряє кожну теку та файли по їх розширенню, організовує сортування файлів, та зміну їх назв


def sort_file(folder, param):
    for i in param.iterdir():
        if i.name in (
            "Documents",
            "Audio",
            "Video",
            "Images",
            "Archives",
            "Other",
        ):
            continue
        if i.is_file():
            flag = False
            for f, suf in suffix_dict.items():
                if i.suffix.lower() in suf:
                    go_dir = Path(folder, f)
                    is_fold_exists(i, go_dir)
                    flag = True
                else:
                    continue
            if not flag:
                go_dir = Path(folder, "other")
                is_fold_exists(i, go_dir)
        elif i.is_dir():
            if len(list(i.iterdir())) != 0:
                sort_file(folder, i)
            else:
                shutil.rmtree(i)
                logger.info(f"Empty folder '{i}' was removed")

    for j in param.iterdir():
        if j.name == "archives" and len(list(j.iterdir())) != 0:
            for arch in j.iterdir():
                if arch.is_file() and arch.suffix in (".zip", ".gz", ".tar"):
                    try:
                        arch_dir_name = arch.resolve().stem
                        path_to_unpack = Path(param, "archives", arch_dir_name)
                        shutil.unpack_archive(arch, path_to_unpack)
                        logger.info(f"Archives '{arch.name}' was unpacked")
                    except:
                        logger.error(f"Error unpacking the archive '{arch.name}'!")
                    finally:
                        continue
                else:
                    continue
        elif j.is_dir() and not len(list(j.iterdir())):
            shutil.rmtree(j)
            logger.info(f"Empty folder '{j}' was removed")


def main():
    logger = get_logger(__name__)

    if len(sys.argv) > 1:
        path = sys.argv[
            1
        ]  # Передаємо шлях до теки, в якій необхідно відсортувати файли

    else:
        print("Please write path to folder")
        exit()

    folder = Path(path)
    p = Path(path)
    try:
        sort_file(folder, p)
    except FileNotFoundError:
        print(
            "\nThe folder was not found. Check the folder's path and run the command again!.\n"
        )
        logger.error(f"The folder with path '{path}' was not found")
    else:
        return show_sort(p)


if __name__ == "__main__":
    main()
