; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c44826396_dispute_amount_sent () Int)
(declare-fun c44826396_fot_fee_deducted_on_deposit () Bool)
(declare-fun c44826396_fot_token_is_dispute_token () Bool)
(declare-fun c44826396_new_tree_publishable () Bool)
(declare-fun c44826396_recovery_path_available () Bool)
(declare-fun c44826396_resolve_dispute_succeeds () Bool)
(assert
 (= c44826396_dispute_amount_sent c44826396_dispute_amount_sent))
(assert
 (= c44826396_fot_fee_deducted_on_deposit c44826396_fot_fee_deducted_on_deposit))
(assert
 (= c44826396_fot_token_is_dispute_token c44826396_fot_token_is_dispute_token))
(assert
 (= c44826396_new_tree_publishable c44826396_new_tree_publishable))
(assert
 (= c44826396_recovery_path_available c44826396_recovery_path_available))
(assert
 (= c44826396_resolve_dispute_succeeds c44826396_resolve_dispute_succeeds))
(define-fun report_preconditions () Bool (and c44826396_fot_token_is_dispute_token
     (= 1000 c44826396_dispute_amount_sent)
     c44826396_fot_fee_deducted_on_deposit
     (not c44826396_recovery_path_available)))
(define-fun report_safety () Bool (=> (and c44826396_fot_token_is_dispute_token
         (= 1000 c44826396_dispute_amount_sent)
         c44826396_fot_fee_deducted_on_deposit
         (not c44826396_recovery_path_available))
    (and c44826396_resolve_dispute_succeeds c44826396_new_tree_publishable)))
(define-fun report_effects () Bool (and c44826396_fot_token_is_dispute_token
     (= 1000 c44826396_dispute_amount_sent)
     c44826396_fot_fee_deducted_on_deposit
     (not c44826396_recovery_path_available)
     (not (and c44826396_resolve_dispute_succeeds
               c44826396_new_tree_publishable))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
