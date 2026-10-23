; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c669a23cb_dispute_posted () Bool)
(declare-fun c669a23cb_dispute_valid () Bool)
(declare-fun c669a23cb_disputer_blacklisted () Bool)
(declare-fun c669a23cb_recorded_resolution_valid () Bool)
(declare-fun c669a23cb_token_blacklistable () Bool)
(declare-fun c669a23cb_tree_incorrect () Bool)
(assert
 (= c669a23cb_dispute_posted c669a23cb_dispute_posted))
(assert
 (= c669a23cb_dispute_valid c669a23cb_dispute_valid))
(assert
 (= c669a23cb_disputer_blacklisted c669a23cb_disputer_blacklisted))
(assert
 (= c669a23cb_recorded_resolution_valid c669a23cb_recorded_resolution_valid))
(assert
 (= c669a23cb_token_blacklistable c669a23cb_token_blacklistable))
(assert
 (= c669a23cb_tree_incorrect c669a23cb_tree_incorrect))
(define-fun report_preconditions () Bool (and c669a23cb_dispute_posted
     c669a23cb_token_blacklistable
     c669a23cb_disputer_blacklisted
     c669a23cb_tree_incorrect))
(define-fun report_safety () Bool (=> (and c669a23cb_dispute_posted
         c669a23cb_tree_incorrect
         c669a23cb_disputer_blacklisted)
    (= c669a23cb_recorded_resolution_valid c669a23cb_dispute_valid)))
(define-fun report_effects () Bool (and c669a23cb_dispute_posted
     c669a23cb_tree_incorrect
     c669a23cb_disputer_blacklisted
     (not (= c669a23cb_recorded_resolution_valid c669a23cb_dispute_valid))))
