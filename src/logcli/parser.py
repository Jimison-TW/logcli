def extract_level(log_line: str) -> str | None:
    """
    字串裡含 "ERROR" 回傳 "ERROR"
    含 "WARN" 回傳 "WARN"
    含 "INFO" 回傳 "INFO"
    都沒有回傳 None
    """

    if "ERROR" in log_line:
        return "ERROR"
    elif "WARN" in log_line:
        return "WARN"
    elif "INFO" in log_line:
        return "INFO"
    else:
        return None
    
def countLevels(lines: list[str]) -> dict[str, int]:
    pass