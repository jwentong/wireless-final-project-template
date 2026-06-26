## Student Information

- Student ID: 2023280502
- Name: 谭榆铃 / Tan Yuling
- GitHub username: tanyuling226
- Fork repository URL: https://github.com/tanyuling226/wireless-final-project-template.git
- Branch: main
- PR number: GitHub will assign this after the Pull Request is created. You may leave it blank first and fill it in after creation.

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

This implementation uses UTF-8 source coding, PN-XOR scrambling, repetition-3 channel coding for the baseline, CRC-protected framing with preamble and length fields, Gray-coded normalized QPSK over AWGN, preamble-correlation synchronization, hard-decision demodulation, and metrics/plot generation.

It also includes documented Level 3 extensions such as Rayleigh fading, OFDM, MRC2 diversity, convolutional Viterbi coding, adaptive modulation, and a local Web demonstration interface. AI assistance was used for design drafting, implementation, testing, debugging, and documentation, with manual review and verification recorded in `AI_LOG.md`.
