; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb7992b3a_claim_rewards_called_before_withdrawal () Bool)
(declare-fun cb7992b3a_ghybr_holds_old_ve_nft () Bool)
(declare-fun cb7992b3a_ghybr_rebase_amount_after_split () Int)
(declare-fun cb7992b3a_ghybr_rebase_amount_before_split () Int)
(assert
 (= cb7992b3a_claim_rewards_called_before_withdrawal cb7992b3a_claim_rewards_called_before_withdrawal))
(assert
 (= cb7992b3a_ghybr_holds_old_ve_nft cb7992b3a_ghybr_holds_old_ve_nft))
(assert
 (= cb7992b3a_ghybr_rebase_amount_after_split cb7992b3a_ghybr_rebase_amount_after_split))
(assert
 (= cb7992b3a_ghybr_rebase_amount_before_split cb7992b3a_ghybr_rebase_amount_before_split))
(define-fun report_preconditions () Bool (and cb7992b3a_ghybr_holds_old_ve_nft
     (not cb7992b3a_claim_rewards_called_before_withdrawal)))
(define-fun report_safety () Bool (=> (< cb7992b3a_ghybr_rebase_amount_after_split
       cb7992b3a_ghybr_rebase_amount_before_split)
    (=> cb7992b3a_ghybr_holds_old_ve_nft
        (= cb7992b3a_ghybr_rebase_amount_after_split
           cb7992b3a_ghybr_rebase_amount_before_split))))
(define-fun report_effects () Bool (and (< cb7992b3a_ghybr_rebase_amount_after_split
        cb7992b3a_ghybr_rebase_amount_before_split)
     cb7992b3a_ghybr_holds_old_ve_nft
     (not (= cb7992b3a_ghybr_rebase_amount_after_split
             cb7992b3a_ghybr_rebase_amount_before_split))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
