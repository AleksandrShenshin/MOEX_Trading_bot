
file_settings = "bot_settings.json"


def create_f_settings() -> int:
    try:
        with open(file_settings, "w", encoding="utf-8") as f:
            # json.dump(signals, f, indent=4, sort_keys=True, ensure_ascii=False)
            print("create_f_settings -- OK")
    except:
        return 1

    return 0