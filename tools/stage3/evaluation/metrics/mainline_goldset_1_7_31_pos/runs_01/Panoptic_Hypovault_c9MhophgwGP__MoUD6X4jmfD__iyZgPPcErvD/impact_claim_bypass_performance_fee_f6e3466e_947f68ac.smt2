; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c883144af_bob_pnl_positive () Bool)
(declare-fun c883144af_fabricated_nonpositive_pnl () Bool)
(declare-fun c883144af_transfer_moves_shares_and_basis () Bool)
(declare-fun c883144af_user_basis_after_transfer () Int)
(declare-fun c883144af_user_basis_before_transfer () Int)
(assert
 (= c883144af_bob_pnl_positive c883144af_bob_pnl_positive))
(assert
 (= c883144af_fabricated_nonpositive_pnl c883144af_fabricated_nonpositive_pnl))
(assert
 (= c883144af_transfer_moves_shares_and_basis c883144af_transfer_moves_shares_and_basis))
(assert
 (= c883144af_user_basis_after_transfer c883144af_user_basis_after_transfer))
(assert
 (= c883144af_user_basis_before_transfer c883144af_user_basis_before_transfer))
(define-fun report_preconditions () Bool (and c883144af_transfer_moves_shares_and_basis c883144af_bob_pnl_positive))
(define-fun report_safety () Bool (=> c883144af_transfer_moves_shares_and_basis
    (= c883144af_user_basis_after_transfer c883144af_user_basis_before_transfer)))
(define-fun report_effects () Bool (and c883144af_transfer_moves_shares_and_basis
     (not (= c883144af_user_basis_after_transfer
             c883144af_user_basis_before_transfer))
     c883144af_fabricated_nonpositive_pnl))
