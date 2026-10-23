; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca50c12d4_end_rewards_completed () Bool)
(declare-fun ca50c12d4_pair_created_with_salt_occurred () Bool)
(declare-fun ca50c12d4_pairfor_computed_from_token0_token1_hash () Bool)
(declare-fun ca50c12d4_rewards_accrual_terminated () Bool)
(assert
 (= ca50c12d4_end_rewards_completed ca50c12d4_end_rewards_completed))
(assert
 (= ca50c12d4_pair_created_with_salt_occurred ca50c12d4_pair_created_with_salt_occurred))
(assert
 (= ca50c12d4_pairfor_computed_from_token0_token1_hash ca50c12d4_pairfor_computed_from_token0_token1_hash))
(assert
 (= ca50c12d4_rewards_accrual_terminated ca50c12d4_rewards_accrual_terminated))
(define-fun report_preconditions () Bool (and ca50c12d4_pair_created_with_salt_occurred
     ca50c12d4_pairfor_computed_from_token0_token1_hash))
(define-fun report_safety () Bool (=> (and ca50c12d4_pair_created_with_salt_occurred
         ca50c12d4_pairfor_computed_from_token0_token1_hash)
    (and ca50c12d4_end_rewards_completed ca50c12d4_rewards_accrual_terminated)))
(define-fun report_effects () Bool (and ca50c12d4_pair_created_with_salt_occurred
     ca50c12d4_pairfor_computed_from_token0_token1_hash
     (not (and ca50c12d4_end_rewards_completed
               ca50c12d4_rewards_accrual_terminated))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
