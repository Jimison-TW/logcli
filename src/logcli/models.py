from dataclasses import dataclass


@dataclass
class LogStats:
    total: int
    error_count: int = 0
    warn_count: int = 0

    @property
    def error_rate(self) -> float:
        return self.error_count / self.total if self.total else 0.0


if __name__ == "__main__":       # ≈ 「這個檔案被直接執行時才跑」，之後會細講
    s = LogStats(total=100)
    print(s)
    print(s.error_rate)

    empty = LogStats(total=0)
    print(empty.error_rate)