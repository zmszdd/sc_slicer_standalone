; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9c420ebb_bond_refunded_to_disputer () Bool)
(declare-fun c9c420ebb_dispute_posted () Bool)
(declare-fun c9c420ebb_dispute_valid () Bool)
(declare-fun c9c420ebb_disputer_blacklisted () Bool)
(declare-fun c9c420ebb_recorded_resolution_valid () Bool)
(declare-fun c9c420ebb_tree_reverted () Bool)
(assert
 (= c9c420ebb_bond_refunded_to_disputer c9c420ebb_bond_refunded_to_disputer))
(assert
 (= c9c420ebb_dispute_posted c9c420ebb_dispute_posted))
(assert
 (= c9c420ebb_dispute_valid c9c420ebb_dispute_valid))
(assert
 (= c9c420ebb_disputer_blacklisted c9c420ebb_disputer_blacklisted))
(assert
 (= c9c420ebb_recorded_resolution_valid c9c420ebb_recorded_resolution_valid))
(assert
 (= c9c420ebb_tree_reverted c9c420ebb_tree_reverted))
(define-fun report_preconditions () Bool (and c9c420ebb_dispute_posted
     c9c420ebb_dispute_valid
     c9c420ebb_disputer_blacklisted))
(define-fun report_safety () Bool (=> (and c9c420ebb_dispute_posted
         c9c420ebb_dispute_valid
         c9c420ebb_disputer_blacklisted)
    (and c9c420ebb_bond_refunded_to_disputer
         c9c420ebb_tree_reverted
         c9c420ebb_recorded_resolution_valid)))
(define-fun report_effects () Bool (and c9c420ebb_dispute_posted
     c9c420ebb_dispute_valid
     c9c420ebb_disputer_blacklisted
     (not (and c9c420ebb_bond_refunded_to_disputer
               c9c420ebb_tree_reverted
               c9c420ebb_recorded_resolution_valid))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
