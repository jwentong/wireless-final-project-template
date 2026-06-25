# Pull Request Information

Suggested PR title:

```text
2024080709-肖佳婷-无线通信期末项目
```

## Student Information

- Student ID: 2024080709
- Name: 肖佳婷
- GitHub username: XJT-ing
- Fork repository URL: https://github.com/XJT-ing/wireless-final-project-template.git
- Branch: main
- PR number: GitHub will assign this after the Pull Request is created.

## Checklist

- [x] I have read `PRD.docx`.
- [x] I have completed `DESIGN.md`.
- [x] I have completed `TEST_PLAN.md`.
- [x] I have completed `MOCK_TEST_REPORT.md`.
- [x] I have completed `AI_LOG.md`.
- [x] The project supports the required command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

- [x] The project generates `results/received.txt`.
- [x] The project generates `results/metrics.json`.
- [x] The project generates at least two required plots.
- [x] I understand the communication principles and code logic of my submission.

## Notes

This submission implements a complete wireless baseband file-transfer simulation. The transmitter converts UTF-8 text to bits, applies PN scrambling, convolutional channel coding, frame building with a pseudo-random preamble, length fields, and CRC, then maps bits to normalized Gray-coded QPSK symbols. The channel uses reproducible AWGN controlled by SNR and seed. The receiver performs preamble-correlation synchronization, QPSK hard demodulation, frame parsing, Viterbi decoding, descrambling, source decoding, and metrics/plot generation.

At `--snr 12 --seed 2026 --mod qpsk --channel awgn`, the generated `results/received.txt` matches `Test.txt`, with `ber = 0.0`, `fer = 0.0`, `text_match_rate = 1.0`, and `checksum_pass = true`.
