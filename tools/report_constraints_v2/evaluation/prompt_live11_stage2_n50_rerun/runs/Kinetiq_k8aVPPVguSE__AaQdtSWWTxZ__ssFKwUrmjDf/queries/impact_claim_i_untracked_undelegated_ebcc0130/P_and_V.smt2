; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd40da1f5_cancelled_withdrawal_amount () Int)
(declare-fun cd40da1f5_manager_has_role () Bool)
(declare-fun cd40da1f5_remainder_nonzero () Bool)
(declare-fun cd40da1f5_stranded_hype_untracked () Bool)
(assert
 (= cd40da1f5_cancelled_withdrawal_amount cd40da1f5_cancelled_withdrawal_amount))
(assert
 (= cd40da1f5_manager_has_role cd40da1f5_manager_has_role))
(assert
 (= cd40da1f5_remainder_nonzero cd40da1f5_remainder_nonzero))
(assert
 (= cd40da1f5_stranded_hype_untracked cd40da1f5_stranded_hype_untracked))
(define-fun report_preconditions () Bool (and (< 0 cd40da1f5_cancelled_withdrawal_amount)
     cd40da1f5_manager_has_role
     cd40da1f5_remainder_nonzero))
(define-fun report_safety () Bool (=> (and cd40da1f5_manager_has_role
         (< 0 cd40da1f5_cancelled_withdrawal_amount)
         cd40da1f5_remainder_nonzero)
    (not cd40da1f5_stranded_hype_untracked)))
(define-fun report_effects () Bool (and cd40da1f5_manager_has_role
     (< 0 cd40da1f5_cancelled_withdrawal_amount)
     cd40da1f5_remainder_nonzero
     (not (not cd40da1f5_stranded_hype_untracked))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
