from typing import Optional
from dataclasses import dataclass, astuple

from bytes_xor import bytes_xor

#obtained from statistical analysis of Frankenstein on ascii_lower
frequencies = {'a': 0.07745577298318623, 'b': 0.01402668189215995, 'c': 0.026667176799173586, 'd': 0.04922288179739303, 'e': 0.13471912790885895, 'f': 0.025036714825137366, 'g': 0.01700801398547888, 'h': 0.05722803805980911, 'i': 0.06296114261833358, 'j': 0.0012684640989343136, 'k': 0.0050885717565137545, 'l': 0.0370562215073827, 'm': 0.03012822965380642, 'n': 0.07127826452921146, 'o': 0.07381519272708009, 'p': 0.017520108540501088, 'q': 0.0009506123061619102, 'r': 0.06110112101618395, 's': 0.061280648417657256, 't': 0.08747693367198284, 'u': 0.030437252230112927, 'v': 0.011139528107810619, 'w': 0.021678669495940033, 'x': 0.001986573704827521, 'y': 0.022841182997283545, 'z': 0.0006268743690789067}

def score_text(text: bytes) -> float:
    score = 0.0
    l = len(text)

    for letter, expected_freq in frequencies.items():
        actual_freq = text.count(ord(letter)) / l
        err = abs(expected_freq - actual_freq)
        score += err

    return score

#allows us to specify # of attributes and build constructor
#that takes all those attributes as arguments
#order=True creates dunder methods (__lt__, __gt__, etc.)
@dataclass(order=True)
class ScoredGuess:
    score: float = float("inf")
    key: Optional[int] = None #int value of repeated byte used as key
    ciphertext: Optional[bytes] = None
    plaintext: Optional[bytes] = None

    @classmethod
    def from_key(cls, ct, key_val):
        full_key = bytes((key_val,)) * len(ct)
        pt = bytes_xor(ct, full_key)
        score = score_text(pt)

        return cls(score, key_val, ct, pt)

def crack_xor_cipher(ct: bytes) -> ScoredGuess:
    best_guess = ScoredGuess()

    ct_len = len(ct)
    ct_freqs = {b: ct.count(b) / ct_len for b in range(256)}

    for candidate_key in range(256):
        score = 0
        for letter, frequency_expected in frequencies.items():
            score += abs(frequency_expected - ct_freqs[ord(letter) ^ candidate_key])
        guess = ScoredGuess(score, candidate_key)
        best_guess = min(best_guess, guess)

    if not best_guess.key:
        exit("no key found (this should never happen!)")

    best_guess.ciphertext = ct
    best_guess.plaintext = bytes_xor(ct, bytes((best_guess.key,) * len(ct)))

    return best_guess

if __name__ == "__main__":
    ciphertext = bytes.fromhex("1b37373331363f78151b7f2b783431333d78397828372d363c78373e783a393b3736")
    best_guess = crack_xor_cipher(ciphertext)
    score, key, ciphertext, plaintext = astuple(best_guess)
    print(f"{key=} | {plaintext=}")

