; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cac55b512_dispute_posted () Bool)
(declare-fun cac55b512_dispute_valid () Bool)
(declare-fun cac55b512_disputer_blacklisted () Bool)
(declare-fun cac55b512_forced_false_event () Bool)
(declare-fun cac55b512_resolved_as_valid () Bool)
(declare-fun cac55b512_token_has_blacklist () Bool)
(assert
 (= cac55b512_dispute_posted cac55b512_dispute_posted))
(assert
 (= cac55b512_dispute_valid cac55b512_dispute_valid))
(assert
 (= cac55b512_disputer_blacklisted cac55b512_disputer_blacklisted))
(assert
 (= cac55b512_forced_false_event cac55b512_forced_false_event))
(assert
 (= cac55b512_resolved_as_valid cac55b512_resolved_as_valid))
(assert
 (= cac55b512_token_has_blacklist cac55b512_token_has_blacklist))
(define-fun report_preconditions () Bool (and cac55b512_dispute_posted
     cac55b512_token_has_blacklist
     cac55b512_disputer_blacklisted
     cac55b512_dispute_valid))
(define-fun report_safety () Bool (=> (and cac55b512_dispute_posted
         cac55b512_token_has_blacklist
         cac55b512_disputer_blacklisted
         cac55b512_dispute_valid)
    (and cac55b512_resolved_as_valid (not cac55b512_forced_false_event))))
(define-fun report_effects () Bool (and cac55b512_dispute_posted
     cac55b512_token_has_blacklist
     cac55b512_disputer_blacklisted
     cac55b512_dispute_valid
     (not (and cac55b512_resolved_as_valid (not cac55b512_forced_false_event)))))
