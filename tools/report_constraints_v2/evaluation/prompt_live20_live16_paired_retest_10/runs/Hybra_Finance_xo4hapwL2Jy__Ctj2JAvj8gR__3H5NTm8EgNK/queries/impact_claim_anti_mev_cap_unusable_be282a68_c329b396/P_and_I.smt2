; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c019af4aa_anti_mev_cap_unusable_occurred () Bool)
(declare-fun c019af4aa_dynamic_fee_within_cap () Bool)
(declare-fun c019af4aa_fee_accepted_by_get_swap_fee () Bool)
(declare-fun c019af4aa_max_fee_cap () Int)
(assert
 (= c019af4aa_anti_mev_cap_unusable_occurred c019af4aa_anti_mev_cap_unusable_occurred))
(assert
 (= c019af4aa_dynamic_fee_within_cap c019af4aa_dynamic_fee_within_cap))
(assert
 (= c019af4aa_fee_accepted_by_get_swap_fee c019af4aa_fee_accepted_by_get_swap_fee))
(assert
 (= c019af4aa_max_fee_cap c019af4aa_max_fee_cap))
(define-fun report_preconditions () Bool (= 500000 c019af4aa_max_fee_cap))
(define-fun report_safety () Bool (=> c019af4aa_dynamic_fee_within_cap c019af4aa_fee_accepted_by_get_swap_fee))
(define-fun report_effects () Bool c019af4aa_anti_mev_cap_unusable_occurred)
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
