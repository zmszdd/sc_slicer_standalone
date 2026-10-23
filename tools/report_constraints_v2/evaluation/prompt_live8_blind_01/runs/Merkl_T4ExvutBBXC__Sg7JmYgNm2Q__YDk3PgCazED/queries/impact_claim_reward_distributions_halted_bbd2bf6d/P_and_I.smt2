; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c99630e0e_disputer_is_set () Bool)
(declare-fun c99630e0e_disputer_reset_on_resolve () Bool)
(declare-fun c99630e0e_set_dispute_amount_reverts () Bool)
(declare-fun c99630e0e_update_tree_accessible () Bool)
(assert
 (= c99630e0e_disputer_is_set c99630e0e_disputer_is_set))
(assert
 (= c99630e0e_disputer_reset_on_resolve c99630e0e_disputer_reset_on_resolve))
(assert
 (= c99630e0e_set_dispute_amount_reverts c99630e0e_set_dispute_amount_reverts))
(assert
 (= c99630e0e_update_tree_accessible c99630e0e_update_tree_accessible))
(define-fun report_preconditions () Bool (and c99630e0e_disputer_is_set
     c99630e0e_disputer_reset_on_resolve
     c99630e0e_set_dispute_amount_reverts))
(define-fun report_safety () Bool (=> c99630e0e_disputer_is_set c99630e0e_update_tree_accessible))
(define-fun report_effects () Bool (and c99630e0e_disputer_is_set (not c99630e0e_update_tree_accessible)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
