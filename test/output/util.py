from amino import List


def myo_syntax(lines: List[str]) -> List[str]:
    return lines.filter(lambda a: a.startswith('Myo')).rstrip


__all__ = ('myo_syntax',)
