from kitty.boss import Boss
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--arg1", dest="tests", action="append")


def main(args: list[str]) -> str:
    opts = parser.parse_args(args[1:])
    # this is the main entry point of the kitten, it will be executed in
    # the overlay window when the kitten is launched
    # answer = input("Enter some text: ")
    answer = str(opts.tests[0])
    # whatever this function returns will be available in the
    # handle_result() function
    return answer


def handle_result(
    args: list[str], answer: str, target_window_id: int, boss: Boss
) -> None:
    # get the kitty window into which to paste answer
    print(args)
    # print(answer)
    w = boss.window_id_map.get(target_window_id)
    # print(w)
    if w is not None:
        w.paste_text(answer)
