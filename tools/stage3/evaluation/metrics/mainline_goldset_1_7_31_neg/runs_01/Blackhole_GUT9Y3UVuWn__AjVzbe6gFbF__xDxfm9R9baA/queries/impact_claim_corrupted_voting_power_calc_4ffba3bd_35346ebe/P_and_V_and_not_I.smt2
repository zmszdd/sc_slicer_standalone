; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c703c8df1_locked_amount_includes_bonus () Bool)
(declare-fun c703c8df1_smnft_balance_expected_base () Int)
(declare-fun c703c8df1_smnft_balance_observed () Int)
(declare-fun c703c8df1_voting_power_corrupted () Bool)
(assert
 (= c703c8df1_locked_amount_includes_bonus c703c8df1_locked_amount_includes_bonus))
(assert
 (= c703c8df1_smnft_balance_expected_base c703c8df1_smnft_balance_expected_base))
(assert
 (= c703c8df1_smnft_balance_observed c703c8df1_smnft_balance_observed))
(assert
 (= c703c8df1_voting_power_corrupted c703c8df1_voting_power_corrupted))
(define-fun report_preconditions () Bool c703c8df1_locked_amount_includes_bonus)
(define-fun report_safety () Bool (=> c703c8df1_locked_amount_includes_bonus
    (= c703c8df1_smnft_balance_observed c703c8df1_smnft_balance_expected_base)))
(define-fun report_effects () Bool (and c703c8df1_locked_amount_includes_bonus
     (not (= c703c8df1_smnft_balance_observed
             c703c8df1_smnft_balance_expected_base))
     c703c8df1_voting_power_corrupted))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
