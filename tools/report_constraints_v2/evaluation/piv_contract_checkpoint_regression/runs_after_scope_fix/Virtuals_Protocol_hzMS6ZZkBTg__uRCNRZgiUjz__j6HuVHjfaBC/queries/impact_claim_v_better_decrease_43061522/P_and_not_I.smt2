; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c93e3e035_better_party_is_b () Bool)
(declare-fun c93e3e035_elo_b_after () Int)
(declare-fun c93e3e035_elo_b_before () Int)
(declare-fun c93e3e035_negative_true () Bool)
(assert
 (= c93e3e035_better_party_is_b c93e3e035_better_party_is_b))
(assert
 (= c93e3e035_elo_b_after c93e3e035_elo_b_after))
(assert
 (= c93e3e035_elo_b_before c93e3e035_elo_b_before))
(assert
 (= c93e3e035_negative_true c93e3e035_negative_true))
(define-fun report_preconditions () Bool c93e3e035_negative_true)
(define-fun report_safety () Bool (=> (and c93e3e035_negative_true c93e3e035_better_party_is_b)
    (< c93e3e035_elo_b_after c93e3e035_elo_b_before)))
(define-fun report_effects () Bool (and c93e3e035_negative_true
     c93e3e035_better_party_is_b
     (not (< c93e3e035_elo_b_after c93e3e035_elo_b_before))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
