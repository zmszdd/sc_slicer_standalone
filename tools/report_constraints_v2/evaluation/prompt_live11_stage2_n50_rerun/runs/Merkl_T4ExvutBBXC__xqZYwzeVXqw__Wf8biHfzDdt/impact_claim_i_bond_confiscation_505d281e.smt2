; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c041b7b51_bond_posted () Bool)
(declare-fun c041b7b51_bond_refunded_to_disputer () Bool)
(declare-fun c041b7b51_disputer_blacklisted () Bool)
(declare-fun c041b7b51_token_blacklistable () Bool)
(declare-fun c041b7b51_tree_incorrect () Bool)
(assert
 (= c041b7b51_bond_posted c041b7b51_bond_posted))
(assert
 (= c041b7b51_bond_refunded_to_disputer c041b7b51_bond_refunded_to_disputer))
(assert
 (= c041b7b51_disputer_blacklisted c041b7b51_disputer_blacklisted))
(assert
 (= c041b7b51_token_blacklistable c041b7b51_token_blacklistable))
(assert
 (= c041b7b51_tree_incorrect c041b7b51_tree_incorrect))
(define-fun report_preconditions () Bool (and c041b7b51_bond_posted
     c041b7b51_token_blacklistable
     c041b7b51_disputer_blacklisted
     c041b7b51_tree_incorrect))
(define-fun report_safety () Bool (=> (and c041b7b51_bond_posted c041b7b51_tree_incorrect)
    c041b7b51_bond_refunded_to_disputer))
(define-fun report_effects () Bool (and c041b7b51_bond_posted
     c041b7b51_tree_incorrect
     (not c041b7b51_bond_refunded_to_disputer)))
