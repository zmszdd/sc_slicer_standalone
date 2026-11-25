; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccf0cd2ba_limit_enforced_on_actual_funds () Bool)
(declare-fun ccf0cd2ba_new_stake_submitted () Bool)
(declare-fun ccf0cd2ba_new_stakes_artificially_limited () Bool)
(declare-fun ccf0cd2ba_slashed_funds_present () Bool)
(assert
 (= ccf0cd2ba_limit_enforced_on_actual_funds ccf0cd2ba_limit_enforced_on_actual_funds))
(assert
 (= ccf0cd2ba_new_stake_submitted ccf0cd2ba_new_stake_submitted))
(assert
 (= ccf0cd2ba_new_stakes_artificially_limited ccf0cd2ba_new_stakes_artificially_limited))
(assert
 (= ccf0cd2ba_slashed_funds_present ccf0cd2ba_slashed_funds_present))
(define-fun report_preconditions () Bool (and ccf0cd2ba_slashed_funds_present ccf0cd2ba_new_stake_submitted))
(define-fun report_safety () Bool (=> ccf0cd2ba_new_stake_submitted ccf0cd2ba_limit_enforced_on_actual_funds))
(define-fun report_effects () Bool (and ccf0cd2ba_new_stake_submitted
     (not ccf0cd2ba_limit_enforced_on_actual_funds)
     ccf0cd2ba_new_stakes_artificially_limited
     ccf0cd2ba_slashed_funds_present))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
