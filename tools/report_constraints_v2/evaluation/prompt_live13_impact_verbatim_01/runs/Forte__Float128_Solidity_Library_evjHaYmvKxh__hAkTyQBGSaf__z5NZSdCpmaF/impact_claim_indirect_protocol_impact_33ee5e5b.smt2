; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9158d661_le_returns_true () Bool)
(declare-fun c9158d661_library_correctness_undermined () Bool)
(declare-fun c9158d661_mantissas_equal () Bool)
(declare-fun c9158d661_packed_representations_differ () Bool)
(declare-fun c9158d661_same_sign_equal_exponents () Bool)
(assert
 (= c9158d661_le_returns_true c9158d661_le_returns_true))
(assert
 (= c9158d661_library_correctness_undermined c9158d661_library_correctness_undermined))
(assert
 (= c9158d661_mantissas_equal c9158d661_mantissas_equal))
(assert
 (= c9158d661_packed_representations_differ c9158d661_packed_representations_differ))
(assert
 (= c9158d661_same_sign_equal_exponents c9158d661_same_sign_equal_exponents))
(define-fun report_preconditions () Bool (and c9158d661_same_sign_equal_exponents
     c9158d661_mantissas_equal
     c9158d661_packed_representations_differ))
(define-fun report_safety () Bool (=> (and c9158d661_same_sign_equal_exponents
         c9158d661_mantissas_equal
         c9158d661_packed_representations_differ)
    (and c9158d661_le_returns_true
         (not c9158d661_library_correctness_undermined))))
(define-fun report_effects () Bool (and c9158d661_same_sign_equal_exponents
     c9158d661_mantissas_equal
     c9158d661_packed_representations_differ
     (not (and c9158d661_le_returns_true
               (not c9158d661_library_correctness_undermined)))))
