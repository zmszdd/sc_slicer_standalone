; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c727b3167_claim_rewards_called_before_withdrawal () Bool)
(declare-fun c727b3167_ghybr_contract_affected_after_split () Bool)
(declare-fun c727b3167_ghybr_holds_old_ve_id () Bool)
(declare-fun c727b3167_ghybr_rebase_amount_after_split () Int)
(declare-fun c727b3167_ghybr_rebase_amount_before_split () Int)
(assert
 (= c727b3167_claim_rewards_called_before_withdrawal c727b3167_claim_rewards_called_before_withdrawal))
(assert
 (= c727b3167_ghybr_contract_affected_after_split c727b3167_ghybr_contract_affected_after_split))
(assert
 (= c727b3167_ghybr_holds_old_ve_id c727b3167_ghybr_holds_old_ve_id))
(assert
 (= c727b3167_ghybr_rebase_amount_after_split c727b3167_ghybr_rebase_amount_after_split))
(assert
 (= c727b3167_ghybr_rebase_amount_before_split c727b3167_ghybr_rebase_amount_before_split))
(define-fun report_preconditions () Bool (and c727b3167_ghybr_holds_old_ve_id
     (not c727b3167_claim_rewards_called_before_withdrawal)))
(define-fun report_safety () Bool (=> c727b3167_ghybr_contract_affected_after_split
    (=> c727b3167_ghybr_holds_old_ve_id
        (= c727b3167_ghybr_rebase_amount_after_split
           c727b3167_ghybr_rebase_amount_before_split))))
(define-fun report_effects () Bool (and c727b3167_ghybr_contract_affected_after_split
     c727b3167_ghybr_holds_old_ve_id
     (not (= c727b3167_ghybr_rebase_amount_after_split
             c727b3167_ghybr_rebase_amount_before_split))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
