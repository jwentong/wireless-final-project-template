from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .channel import awgn, equalize_flat_rayleigh, rayleigh_flat, rayleigh_mrc2
from .channel_coding import channel_decode, channel_encode
from .convolutional import conv_encode, viterbi_decode
from .crypto import descramble, scramble
from .framing import PREAMBLE_BITS, build_frame, crc32_bits, parse_frame
from .modulation import demodulate_symbols, modulate_bits, qpsk_demodulate, qpsk_modulate, select_adaptive_modulation
from .ofdm import ofdm_demodulate, ofdm_modulate
from .source import source_decode, source_encode
from .synchronization import detect_frame_start


OFDM_FFT_SIZE = 64
OFDM_CP_LEN = 16


def bit_error_rate(expected: list[int], actual: list[int]) -> float:
    n = min(len(expected), len(actual))
    if n == 0:
        return 0.0 if len(expected) == len(actual) else 1.0
    errors = sum(int(a) != int(b) for a, b in zip(expected[:n], actual[:n]))
    errors += abs(len(expected) - len(actual))
    return errors / max(len(expected), len(actual))


def text_match_rate(expected: str, actual: str) -> float:
    if not expected and not actual:
        return 1.0
    n = min(len(expected), len(actual))
    matches = sum(a == b for a, b in zip(expected[:n], actual[:n]))
    return matches / max(len(expected), len(actual), 1)


def _bit_preview(bits: list[int], limit: int = 48) -> str:
    shown = "".join(str(int(bit)) for bit in bits[:limit])
    return shown + ("..." if len(bits) > limit else "")


def _stage(name: str, detail: str, **values) -> dict[str, object]:
    item: dict[str, object] = {"name": name, "detail": detail}
    item.update(values)
    return item


def _apply_scramble(bits: list[int], mode: str, seed: int) -> list[int]:
    if mode == "pn-xor":
        return scramble(bits, seed=seed)
    if mode == "none":
        return bits.copy()
    raise ValueError("supported scramble modes: pn-xor, none")


def _apply_descramble(bits: list[int], mode: str, seed: int) -> list[int]:
    if mode == "pn-xor":
        return descramble(bits, seed=seed)
    if mode == "none":
        return bits.copy()
    raise ValueError("supported scramble modes: pn-xor, none")


def _apply_channel_encode(bits: list[int], mode: str) -> list[int]:
    if mode == "repetition3":
        return channel_encode(bits)
    if mode == "conv":
        return conv_encode(bits)
    if mode == "none":
        return bits.copy()
    raise ValueError("supported channel coding modes: repetition3, conv, none")


def _apply_channel_decode(bits: list[int], mode: str) -> list[int]:
    if mode == "repetition3":
        return channel_decode(bits)
    if mode == "conv":
        return viterbi_decode(bits)
    if mode == "none":
        return bits.copy()
    raise ValueError("supported channel coding modes: repetition3, conv, none")


def _channel_code_label(mode: str) -> str:
    if mode == "repetition3":
        return "repetition-3"
    if mode == "conv":
        return "convolutional-viterbi"
    return "none"


def _write_plots(results_dir: Path, received_symbols, synchronized_symbols, corr, seed: int) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    constellation = np.asarray(synchronized_symbols[: min(400, len(synchronized_symbols))], dtype=complex)
    if constellation.size:
        plt.figure(figsize=(5, 5))
        plt.scatter(constellation.real, constellation.imag, s=12, alpha=0.65)
        plt.axhline(0, color="0.7", linewidth=0.8)
        plt.axvline(0, color="0.7", linewidth=0.8)
        plt.xlabel("In-phase")
        plt.ylabel("Quadrature")
        plt.title("Received Constellation")
        plt.grid(True, alpha=0.25)
        plt.tight_layout()
        plt.savefig(results_dir / "constellation.png", dpi=150)
        plt.close()
    if len(corr):
        plt.figure(figsize=(7, 4))
        plt.plot(corr)
        plt.xlabel("Candidate start index")
        plt.ylabel("Correlation magnitude")
        plt.title("Synchronization Peak")
        plt.grid(True, alpha=0.25)
        plt.tight_layout()
        plt.savefig(results_dir / "sync_peak.png", dpi=150)
        plt.close()
    snrs = [0, 3, 6, 9, 12, 15]
    rng_bits = [int(x) for x in np.random.default_rng(seed).integers(0, 2, size=1200)]
    tx = qpsk_modulate(rng_bits)
    bers: list[float] = []
    for snr in snrs:
        rx = awgn(tx, snr_db=snr, seed=seed + snr)
        demod = qpsk_demodulate(rx)[: len(rng_bits)]
        bers.append(bit_error_rate(rng_bits, demod))
    plt.figure(figsize=(7, 4))
    plt.semilogy(snrs, [max(v, 1e-5) for v in bers], marker="o")
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.title("QPSK AWGN BER-SNR Curve")
    plt.grid(True, which="both", alpha=0.25)
    plt.tight_layout()
    plt.savefig(results_dir / "ber_curve.png", dpi=150)
    plt.close()


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    snr_db: float = 12.0,
    seed: int = 2026,
    modulation: str = "qpsk",
    channel_name: str = "awgn",
    source_codec: str = "utf8",
    scramble_mode: str = "pn-xor",
    coding_mode: str = "repetition3",
    diversity: str = "none",
    ofdm_enabled: bool = False,
) -> dict[str, object]:
    requested_modulation = modulation.lower()
    if requested_modulation == "adaptive":
        effective_modulation = select_adaptive_modulation(snr_db)
    elif requested_modulation in {"bpsk", "qpsk", "16qam"}:
        effective_modulation = requested_modulation
    else:
        raise ValueError("supported modulation: bpsk, qpsk, 16qam, adaptive")
    if source_codec.lower() != "utf8":
        raise ValueError("supported source codec: utf8")
    channel_mode = channel_name.lower()
    if channel_mode not in {"awgn", "rayleigh"}:
        raise ValueError("supported channels: awgn, rayleigh")
    diversity_mode = diversity.lower()
    if diversity_mode not in {"none", "mrc2"}:
        raise ValueError("supported diversity modes: none, mrc2")
    if diversity_mode == "mrc2" and channel_mode != "rayleigh":
        raise ValueError("mrc2 diversity is supported with rayleigh channel")

    input_path = Path(input_path)
    output_path = Path(output_path)
    results_dir = output_path.parent
    results_dir.mkdir(parents=True, exist_ok=True)

    text = input_path.read_text(encoding="utf-8")
    source_bits = source_encode(text)
    stage_trace: list[dict[str, object]] = [
        _stage(
            "Source Encode",
            "UTF-8 text is converted to a big-endian bitstream.",
            input_chars=len(text),
            output_bits=len(source_bits),
            preview=_bit_preview(source_bits),
        )
    ]
    scramble_mode = scramble_mode.lower()
    coding_mode = coding_mode.lower()
    scrambled = _apply_scramble(source_bits, scramble_mode, seed=seed)
    stage_trace.append(
        _stage(
            "Scramble / Encrypt",
            "PN XOR scrambling is reversible; demo mode can disable it.",
            mode=scramble_mode,
            input_bits=len(source_bits),
            output_bits=len(scrambled),
            preview=_bit_preview(scrambled),
        )
    )
    coded = _apply_channel_encode(scrambled, coding_mode)
    code_rate = 1.0 if coding_mode == "none" else len(scrambled) / max(len(coded), 1)
    stage_trace.append(
        _stage(
            "Channel Encode",
            "Selected FEC adds redundancy before framing.",
            mode=coding_mode,
            input_bits=len(scrambled),
            output_bits=len(coded),
            code_rate=code_rate,
            preview=_bit_preview(coded),
        )
    )
    frame = build_frame(coded, tx_payload_bits=len(coded), original_payload_bits=source_bits)
    stage_trace.append(
        _stage(
            "Frame Build",
            "Frame adds preamble, original payload length, transmitted payload length, coded payload, and CRC over original payload bits.",
            preamble_bits=len(PREAMBLE_BITS),
            payload_bits=len(source_bits),
            tx_payload_bits=len(coded),
            frame_bits=len(frame["bits"]),
            checksum_bits=32,
            checksum_scope=frame["checksum_scope"],
        )
    )
    tx_symbols = modulate_bits(frame["bits"], effective_modulation)
    preamble_symbols = modulate_bits(PREAMBLE_BITS, effective_modulation)
    stage_trace.append(
        _stage(
            "QPSK Modulate" if effective_modulation == "qpsk" else "Modulate",
            "Bits are mapped to normalized constellation symbols.",
            requested_modulation=requested_modulation,
            effective_modulation=effective_modulation,
            input_bits=len(frame["bits"]),
            output_symbols=int(len(tx_symbols)),
        )
    )

    if ofdm_enabled:
        tx_waveform, ofdm_padded_symbols = ofdm_modulate(tx_symbols, fft_size=OFDM_FFT_SIZE, cp_len=OFDM_CP_LEN)
        sync_reference = qpsk_modulate(PREAMBLE_BITS)
        payload_waveform = np.concatenate([sync_reference, tx_waveform])
        stage_trace.append(
            _stage(
                "OFDM Modulate",
                "Constellation symbols are packed onto OFDM subcarriers with a cyclic prefix.",
                fft_size=OFDM_FFT_SIZE,
                cp_len=OFDM_CP_LEN,
                data_symbols=int(len(tx_symbols)),
                padded_symbols=int(ofdm_padded_symbols),
                waveform_samples=int(len(payload_waveform)),
            )
        )
    else:
        sync_reference = preamble_symbols
        payload_waveform = tx_symbols
        ofdm_padded_symbols = len(tx_symbols)

    rng = np.random.default_rng(seed)
    prefix_len = int(rng.integers(0, 129))
    prefix = (rng.normal(size=prefix_len) + 1j * rng.normal(size=prefix_len)) / np.sqrt(2)
    channel_input = np.concatenate([prefix, payload_waveform])
    rayleigh_gain = None
    diversity_gains: tuple[complex, complex] | None = None
    equalizer = "none"
    if channel_mode == "awgn":
        received = awgn(channel_input, snr_db=snr_db, seed=seed + 1)
    elif diversity_mode == "mrc2":
        received, diversity_gains = rayleigh_mrc2(channel_input, snr_db=snr_db, seed=seed + 1)
        equalizer = "mrc2"
    else:
        received, rayleigh_gain = rayleigh_flat(channel_input, snr_db=snr_db, seed=seed + 1, return_gain=True)
        received = equalize_flat_rayleigh(received, rayleigh_gain)
        equalizer = "perfect-csi-one-tap"
    stage_trace.append(
        _stage(
            "Wireless Channel",
            "Random prefix offset is inserted before channel simulation.",
            channel=channel_mode,
            snr_db=float(snr_db),
            prefix_symbols=prefix_len,
            received_symbols=int(len(received)),
            equalizer=equalizer,
            diversity=diversity_mode,
        )
    )

    sync = detect_frame_start(received, preamble=sync_reference)
    start = int(sync["start_index"])
    stage_trace.append(
        _stage(
            "Synchronization",
            "Receiver searches the preamble correlation peak instead of assuming the frame start.",
            detected_start=start,
            expected_start=prefix_len,
            error_symbols=int(start - prefix_len),
            peak_value=float(sync["peak_value"]),
        )
    )
    if ofdm_enabled:
        ofdm_start = start + len(sync_reference)
        synchronized_waveform = received[ofdm_start : ofdm_start + len(tx_waveform)]
        synchronized_symbols = ofdm_demodulate(
            synchronized_waveform,
            symbol_count=len(tx_symbols),
            fft_size=OFDM_FFT_SIZE,
            cp_len=OFDM_CP_LEN,
        )
        constellation_for_plot = synchronized_symbols
        stage_trace.append(
            _stage(
                "OFDM Demodulate",
                "Cyclic prefixes are removed and FFT restores data subcarrier symbols.",
                input_samples=int(len(synchronized_waveform)),
                output_symbols=int(len(synchronized_symbols)),
            )
        )
    else:
        synchronized_symbols = received[start : start + len(tx_symbols)]
        constellation_for_plot = synchronized_symbols
    demod_bits = demodulate_symbols(synchronized_symbols, effective_modulation)
    stage_trace.append(
        _stage(
            "QPSK Demodulate" if effective_modulation == "qpsk" else "Demodulate",
            "Hard decisions map each received constellation point back to bits.",
            input_symbols=int(len(synchronized_symbols)),
            output_bits=len(demod_bits),
            preview=_bit_preview(demod_bits),
        )
    )
    parsed = parse_frame(demod_bits)
    received_coded = parsed["payload"][: int(parsed["tx_length"])]
    decoded_bits = _apply_channel_decode(received_coded, coding_mode)
    stage_trace.append(
        _stage(
            "Channel Decode",
            "The receiver applies the selected FEC decoder.",
            mode=coding_mode,
            input_bits=len(received_coded),
            output_bits=len(decoded_bits),
            preview=_bit_preview(decoded_bits),
        )
    )
    original_length = int(parsed["length"])
    descrambled_bits = _apply_descramble(decoded_bits, scramble_mode, seed=seed)[:original_length]
    stage_trace.append(
        _stage(
            "Descramble / Decrypt",
            "The receiver applies the same PN XOR sequence to recover original source bits.",
            mode=scramble_mode,
            input_bits=len(decoded_bits),
            output_bits=len(descrambled_bits),
            preview=_bit_preview(descrambled_bits),
        )
    )

    decode_error = None
    try:
        recovered_text = source_decode(descrambled_bits)
    except UnicodeDecodeError as exc:
        decode_error = str(exc)
        recovered_text = source_decode([0] * ((len(source_bits) // 8) * 8))
    output_path.write_text(recovered_text, encoding="utf-8")
    stage_trace.append(
        _stage(
            "Source Decode",
            "Recovered source bits are converted back to UTF-8 text.",
            input_bits=len(descrambled_bits),
            output_chars=len(recovered_text),
            decode_error=decode_error,
        )
    )

    ber = bit_error_rate(source_bits, descrambled_bits)
    match_rate = text_match_rate(text, recovered_text)
    payload_checksum_pass = parsed["checksum"] == crc32_bits(descrambled_bits[:original_length])
    recovered_bits_match = source_bits == descrambled_bits[: len(source_bits)]
    stage_trace.append(
        _stage(
            "Metrics / Plots",
            "The simulator writes received.txt, metrics.json, constellation, BER-SNR, and synchronization plots.",
            ber=float(ber),
            text_match_rate=float(match_rate),
            checksum_pass=bool(payload_checksum_pass),
        )
    )
    metrics = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": effective_modulation,
        "requested_modulation": requested_modulation,
        "effective_modulation": effective_modulation,
        "channel": channel_mode,
        "payload_bits": len(source_bits),
        "ber": float(ber),
        "fer": 0.0 if payload_checksum_pass and match_rate == 1.0 else 1.0,
        "text_match_rate": float(match_rate),
        "checksum_pass": bool(payload_checksum_pass and recovered_bits_match),
        "sync_start_index": start,
        "sync_expected_offset": prefix_len,
        "sync_error_symbols": int(start - prefix_len),
        "source_codec": "utf8",
        "channel_code": _channel_code_label(coding_mode),
        "scrambler": "xor-pn-sequence" if scramble_mode == "pn-xor" else "none",
        "equalizer": equalizer,
        "diversity": diversity_mode,
        "ofdm_enabled": bool(ofdm_enabled),
        "ofdm_fft_size": OFDM_FFT_SIZE if ofdm_enabled else None,
        "ofdm_cp_len": OFDM_CP_LEN if ofdm_enabled else None,
        "rayleigh_gain_real": None if rayleigh_gain is None else float(np.real(rayleigh_gain)),
        "rayleigh_gain_imag": None if rayleigh_gain is None else float(np.imag(rayleigh_gain)),
        "diversity_gain_1_real": None if diversity_gains is None else float(np.real(diversity_gains[0])),
        "diversity_gain_1_imag": None if diversity_gains is None else float(np.imag(diversity_gains[0])),
        "diversity_gain_2_real": None if diversity_gains is None else float(np.real(diversity_gains[1])),
        "diversity_gain_2_imag": None if diversity_gains is None else float(np.imag(diversity_gains[1])),
        "frame_payload_bits": int(parsed["length"]),
        "frame_transmitted_payload_bits": int(parsed["tx_length"]),
        "frame_crc_scope": "original-payload-bits",
        "frame_crc_pass": bool(payload_checksum_pass),
        "frame_crc_pass_before_fec": None,
        "failure_reason": decode_error or (None if match_rate == 1.0 and payload_checksum_pass else "bit errors or checksum failure"),
        "stage_trace": stage_trace,
    }
    (results_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_plots(results_dir, received, constellation_for_plot, sync["correlation"], seed=seed)
    return metrics


