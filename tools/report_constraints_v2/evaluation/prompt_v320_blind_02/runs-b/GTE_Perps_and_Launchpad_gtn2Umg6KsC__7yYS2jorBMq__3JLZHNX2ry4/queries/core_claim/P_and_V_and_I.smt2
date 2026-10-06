; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun pair_is_set () Bool)
(declare-fun total_fee_share () Int)
(declare-fun rewards_phase_closed () Bool)
(assert
 (= pair_is_set pair_is_set))
(assert
 (= total_fee_share total_fee_share))
(assert
 (= rewards_phase_closed rewards_phase_closed))
(define-fun report_preconditions () Bool (and (not pair_is_set) (= 0 total_fee_share)))
(define-fun report_safety () Bool (=> (and (not pair_is_set) (= 0 total_fee_share)) (not rewards_phase_closed)))
(define-fun report_effects () Bool (and (not pair_is_set) (= 0 total_fee_share) (not (not rewards_phase_closed))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
