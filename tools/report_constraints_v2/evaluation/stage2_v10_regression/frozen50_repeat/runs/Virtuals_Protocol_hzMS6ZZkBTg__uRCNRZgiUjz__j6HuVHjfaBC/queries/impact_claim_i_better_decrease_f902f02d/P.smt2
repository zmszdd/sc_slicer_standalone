; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0744c346_better_party_rating_decreased () Bool)
(declare-fun c0744c346_negative () Bool)
(assert
 (= c0744c346_better_party_rating_decreased c0744c346_better_party_rating_decreased))
(assert
 (= c0744c346_negative c0744c346_negative))
(define-fun report_preconditions () Bool (and c0744c346_negative (not c0744c346_negative)))
(define-fun report_safety () Bool (=> c0744c346_negative (not c0744c346_better_party_rating_decreased)))
(define-fun report_effects () Bool (and c0744c346_negative (not (not c0744c346_better_party_rating_decreased))))
(assert report_preconditions)
(check-sat)
