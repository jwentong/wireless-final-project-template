import argparse

from src.pipeline import run_system


def parse_args():
    parser = argparse.ArgumentParser(description="Wireless baseband file-transfer simulation")
    parser.add_argument("--input", required=True, help="UTF-8 input text file")
    parser.add_argument("--output", required=True, help="Recovered output text file")
    parser.add_argument("--snr", type=float, default=12.0, help="AWGN SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", default="qpsk", help="Modulation, base system supports qpsk")
    parser.add_argument("--channel", default="awgn", help="Channel, base system supports awgn")
    return parser.parse_args()


def main():
    args = parse_args()
    metrics = run_system(
        input_path=args.input,
        output_path=args.output,
        snr_db=args.snr,
        seed=args.seed,
        modulation=args.mod,
        channel=args.channel,
    )
    print(f"received={args.output} ber={metrics['ber']:.6g} text_match_rate={metrics['text_match_rate']:.3f}")


if __name__ == "__main__":
    main()

