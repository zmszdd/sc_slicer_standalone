; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5ad7ccde_funds_stuck_in_manager () Bool)
(declare-fun c5ad7ccde_pool_live_weight () Int)
(declare-fun c5ad7ccde_rewards_transferred () Bool)
(declare-fun c5ad7ccde_total_weight () Int)
(assert
 (= c5ad7ccde_funds_stuck_in_manager c5ad7ccde_funds_stuck_in_manager))
(assert
 (= c5ad7ccde_pool_live_weight c5ad7ccde_pool_live_weight))
(assert
 (= c5ad7ccde_rewards_transferred c5ad7ccde_rewards_transferred))
(assert
 (= c5ad7ccde_total_weight c5ad7ccde_total_weight))
(define-fun report_preconditions () Bool (and (= 0 c5ad7ccde_total_weight) (= 0 c5ad7ccde_pool_live_weight)))
(define-fun report_safety () Bool (=> (and c5ad7ccde_rewards_transferred
         (= 0 c5ad7ccde_total_weight)
         (= 0 c5ad7ccde_pool_live_weight))
    (not c5ad7ccde_funds_stuck_in_manager)))
(define-fun report_effects () Bool (and c5ad7ccde_rewards_transferred
     (= 0 c5ad7ccde_total_weight)
     (= 0 c5ad7ccde_pool_live_weight)
     (not (not c5ad7ccde_funds_stuck_in_manager))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
