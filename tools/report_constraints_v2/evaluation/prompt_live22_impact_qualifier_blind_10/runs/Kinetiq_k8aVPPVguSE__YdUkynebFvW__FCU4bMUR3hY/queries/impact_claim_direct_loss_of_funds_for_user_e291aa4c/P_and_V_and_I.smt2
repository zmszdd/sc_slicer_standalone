; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2ccd15e4_hype_received () Int)
(declare-fun c2ccd15e4_khype_shares_provided () Int)
(declare-fun c2ccd15e4_min_hype_bound_enforced () Bool)
(declare-fun c2ccd15e4_slashing_amount () Int)
(declare-fun c2ccd15e4_slashing_reported_before_queue () Bool)
(declare-fun c2ccd15e4_user_expected_hype () Int)
(assert
 (= c2ccd15e4_hype_received c2ccd15e4_hype_received))
(assert
 (= c2ccd15e4_khype_shares_provided c2ccd15e4_khype_shares_provided))
(assert
 (= c2ccd15e4_min_hype_bound_enforced c2ccd15e4_min_hype_bound_enforced))
(assert
 (= c2ccd15e4_slashing_amount c2ccd15e4_slashing_amount))
(assert
 (= c2ccd15e4_slashing_reported_before_queue c2ccd15e4_slashing_reported_before_queue))
(assert
 (= c2ccd15e4_user_expected_hype c2ccd15e4_user_expected_hype))
(define-fun report_preconditions () Bool (and (< 0 c2ccd15e4_khype_shares_provided)
     (<= 0 c2ccd15e4_slashing_amount)
     c2ccd15e4_slashing_reported_before_queue))
(define-fun report_safety () Bool (=> (and (< c2ccd15e4_hype_received c2ccd15e4_user_expected_hype)
         (not c2ccd15e4_min_hype_bound_enforced))
    (=> (and (< 0 c2ccd15e4_khype_shares_provided)
             c2ccd15e4_slashing_reported_before_queue)
        (and c2ccd15e4_min_hype_bound_enforced
             (>= c2ccd15e4_hype_received c2ccd15e4_user_expected_hype)))))
(define-fun report_effects () Bool (and (< c2ccd15e4_hype_received c2ccd15e4_user_expected_hype)
     (not c2ccd15e4_min_hype_bound_enforced)
     (< 0 c2ccd15e4_khype_shares_provided)
     c2ccd15e4_slashing_reported_before_queue
     (not (and c2ccd15e4_min_hype_bound_enforced
               (>= c2ccd15e4_hype_received c2ccd15e4_user_expected_hype)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
