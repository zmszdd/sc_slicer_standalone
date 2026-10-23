; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfbeec899_le_returns_false_on_equal () Bool)
(declare-fun cfbeec899_mantissas_equal () Bool)
(declare-fun cfbeec899_packed_representations_differ () Bool)
(declare-fun cfbeec899_same_sign_equal_exponents () Bool)
(assert
 (= cfbeec899_le_returns_false_on_equal cfbeec899_le_returns_false_on_equal))
(assert
 (= cfbeec899_mantissas_equal cfbeec899_mantissas_equal))
(assert
 (= cfbeec899_packed_representations_differ cfbeec899_packed_representations_differ))
(assert
 (= cfbeec899_same_sign_equal_exponents cfbeec899_same_sign_equal_exponents))
(define-fun report_preconditions () Bool (and cfbeec899_same_sign_equal_exponents
     cfbeec899_mantissas_equal
     cfbeec899_packed_representations_differ))
(define-fun report_safety () Bool (=> (and cfbeec899_same_sign_equal_exponents
         cfbeec899_mantissas_equal
         cfbeec899_packed_representations_differ)
    (not cfbeec899_le_returns_false_on_equal)))
(define-fun report_effects () Bool (and cfbeec899_same_sign_equal_exponents
     cfbeec899_mantissas_equal
     cfbeec899_packed_representations_differ
     (not (not cfbeec899_le_returns_false_on_equal))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
