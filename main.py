import argparse
import sys

from src.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wireless communication baseband simulation")
    parser.add_argument("--input", required=True, help="Input UTF-8 text file, e.g. Test.txt")
    parser.add_argument("--output", required=True, help="Output received text file, e.g. results/received.txt")
    parser.add_argument("--snr", required=True, type=float, help="AWGN SNR in dB")
    parser.add_argument("--seed", required=True, type=int, help="Random seed")
    parser.add_argument("--mod", default="qpsk", help="Modulation, base requirement: qpsk")
    parser.add_argument("--channel", default="awgn", help="Channel, base requirement: awgn")
    parser.add_argument("--fec", default="repetition", help="FEC: repetition or conv")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metrics = run_pipeline(args.input, args.output, args.snr, args.seed, args.mod, args.channel, args.fec)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        "completed: "
        f"ber={metrics['ber']:.6g}, fer={metrics['fer']:.6g}, "
        f"text_match_rate={metrics['text_match_rate']:.6g}, "
        f"checksum_pass={metrics['checksum_pass']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
