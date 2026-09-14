# Заготовка: полная версия после разведки (probe.py).
import sys


def keep_old(before, after):
    """Старые цены сети остаются, если собрано меньше 30% прошлого покрытия."""
    return before > 0 and after < before * 0.3


if __name__ == "__main__":
    assert keep_old(20, 5) and not keep_old(20, 6) and not keep_old(0, 0)
    if "--check" in sys.argv:
        print("update_all self-check ok")
