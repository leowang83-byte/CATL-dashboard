import argostranslate.package
import argostranslate.translate


def main():
    print("Updating Argos package index...")
    argostranslate.package.update_package_index()

    available_packages = argostranslate.package.get_available_packages()

    target_package = None

    for package in available_packages:
        if package.from_code == "en" and package.to_code == "zh":
            target_package = package
            break

    if target_package is None:
        print("没有找到 en -> zh 翻译包。")
        print("可用包示例：")
        for package in available_packages[:20]:
            print(package.from_code, "->", package.to_code)
        return

    print("Found package:", target_package)
    print("Downloading package...")
    package_path = target_package.download()

    print("Installing package...")
    argostranslate.package.install_from_path(package_path)

    print("Testing translation...")
    translated = argostranslate.translate.translate(
        "SQM Reports Earnings for the Three Months Ended March 31, 2026",
        "en",
        "zh",
    )

    print("Result:", translated)


if __name__ == "__main__":
    main()