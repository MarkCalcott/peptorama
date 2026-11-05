
def stereo_eq(a_stereo: str, b_stereo: str, mode: str) -> bool:
    """Are two stereochemistry values equivalent under the given mode?"""
    if mode == "relaxed":
        return True
    if mode == "strict":
        return a_stereo == b_stereo
    # Moderate mode flat is True
    if a_stereo == "flat" or b_stereo == "flat":
        return True
    return a_stereo == b_stereo


def make_match_fn(stereo_mode: str):
    """
    Return a function that decides whether two (residue, stereo) tuples match
    under the given stereo mode. Residue identity must always be equal; the
    stereo comparison varies by mode.
    """
    def match(a: tuple[str, str], b: tuple[str, str]) -> bool:
        residue_a, stereo_a = a
        residue_b, stereo_b = b
        return residue_a == residue_b and stereo_eq(stereo_a, stereo_b, stereo_mode)
    return match

def make_score_fn(stereo_mode: str, match_score: int = 1, mismatch_score: int = -1):
    """
    Return a scoring function for Needleman-Wunsch under the given stereo mode.
    The function takes two (residue, stereo) tuples and returns a numeric score.
    """
    match_fn = make_match_fn(stereo_mode)
    def score_fn(a, b):
        return match_score if match_fn(a, b) else mismatch_score
    return score_fn

def needleman_wunsch(sequence1, sequence2, score_fn, gap = -1):
    """ 
    Perform Needleman-Wunsch alignment on two sequences.
     
    The sequences are anything separated into a list by the given 
    sequence_parser. This allows alignment of sequences not defined by single
    letters and the separation can be by things like commas or more complex.
    
    Original method: Needleman, S. B., & Wunsch, C. D. (1970). A general method 
    applicable to the search for similarities in the amino acid sequence of two 
    proteins. Journal of molecular biology, 48(3), 443-453.
    """

    m, n = len(sequence1), len(sequence2)
    # Initialize scoring and traceback matrix
    score = [[0] * (n + 1) for _ in range(m + 1)]
    traceback = [[None] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        score[i][0] = i * gap
        traceback[i][0] = ['U']  # Up
    for j in range(n + 1):
        score[0][j] = j * gap
        traceback[0][j] = ['L']  # Left

    # Fill scoring matrix
    for i in range(m):
        for j in range(n):
            top_left = score[i][j] + score_fn(sequence1[i], sequence2[j])
            left = score[i + 1][j] + gap
            top = score[i][j + 1] + gap

            score[i + 1][j + 1] = max(top_left, top, left)

            if score[i + 1][j + 1] == top_left:
                traceback[i + 1][j + 1] = ['D']  # Diagonal
            elif score[i + 1][j + 1] == top:
                traceback[i + 1][j + 1] = ['U']  # Up
            else:
                traceback[i + 1][j + 1] = ['L']  # Left

    # Traceback
    code = []

    while m > 0 or n > 0:

        string1 = sequence1[m - 1]
        string2 = sequence2[n - 1]

        if traceback[m][n] == ['D']:
            code.append("=" if score_fn(sequence1[m - 1], sequence2[n- 1]) > 0 else "≠")
            m -= 1
            n -= 1
        elif traceback[m][n] == ['U']:
            code.append("1")
            m -= 1
        elif traceback[m][n] == ['L']:
            code.append("2")
            n -= 1

    return "".join(reversed(code))
