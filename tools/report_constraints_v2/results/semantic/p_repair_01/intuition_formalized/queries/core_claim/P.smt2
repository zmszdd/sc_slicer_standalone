; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun curve_initialized_with_low_offset () Bool)
(declare-fun offset18 () Int)
(declare-fun user_has_deposit () Bool)
(declare-fun withdrawal_reverts () Bool)
(assert
 (= curve_initialized_with_low_offset curve_initialized_with_low_offset))
(assert
 (= offset18 offset18))
(assert
 (= user_has_deposit user_has_deposit))
(assert
 (= withdrawal_reverts withdrawal_reverts))
(define-fun report_preconditions () Bool (and curve_initialized_with_low_offset
     (> 1000000000000000000 offset18)
     user_has_deposit))
(define-fun report_safety () Bool (=> curve_initialized_with_low_offset (not withdrawal_reverts)))
(define-fun report_effects () Bool (and curve_initialized_with_low_offset withdrawal_reverts))
(assert report_preconditions)
(check-sat)
(get-model)
