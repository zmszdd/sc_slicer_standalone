; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7012e3ed_locked_amount_includes_bonus () Bool)
(declare-fun c7012e3ed_smnft_balance_expected_base () Int)
(declare-fun c7012e3ed_smnft_balance_observed () Int)
(assert
 (= c7012e3ed_locked_amount_includes_bonus c7012e3ed_locked_amount_includes_bonus))
(assert
 (= c7012e3ed_smnft_balance_expected_base c7012e3ed_smnft_balance_expected_base))
(assert
 (= c7012e3ed_smnft_balance_observed c7012e3ed_smnft_balance_observed))
(define-fun report_preconditions () Bool c7012e3ed_locked_amount_includes_bonus)
(define-fun report_safety () Bool (=> c7012e3ed_locked_amount_includes_bonus
    (= c7012e3ed_smnft_balance_observed c7012e3ed_smnft_balance_expected_base)))
(define-fun report_effects () Bool (and c7012e3ed_locked_amount_includes_bonus
     (not (= c7012e3ed_smnft_balance_observed
             c7012e3ed_smnft_balance_expected_base))
     (> c7012e3ed_smnft_balance_observed c7012e3ed_smnft_balance_expected_base)))
(assert report_preconditions)
(check-sat)
(get-model)
