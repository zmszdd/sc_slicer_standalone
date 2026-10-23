; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c103a8f5a_end_rewards_completes () Bool)
(declare-fun c103a8f5a_end_rewards_reverts_occurred () Bool)
(declare-fun c103a8f5a_pair_created_with_salt_included () Bool)
(declare-fun c103a8f5a_pairfor_inputs_token0_token1_hash () Bool)
(assert
 (= c103a8f5a_end_rewards_completes c103a8f5a_end_rewards_completes))
(assert
 (= c103a8f5a_end_rewards_reverts_occurred c103a8f5a_end_rewards_reverts_occurred))
(assert
 (= c103a8f5a_pair_created_with_salt_included c103a8f5a_pair_created_with_salt_included))
(assert
 (= c103a8f5a_pairfor_inputs_token0_token1_hash c103a8f5a_pairfor_inputs_token0_token1_hash))
(define-fun report_preconditions () Bool (and c103a8f5a_pair_created_with_salt_included
     c103a8f5a_pairfor_inputs_token0_token1_hash))
(define-fun report_safety () Bool (=> (and c103a8f5a_pair_created_with_salt_included
         c103a8f5a_pairfor_inputs_token0_token1_hash)
    (and c103a8f5a_end_rewards_completes
         (not c103a8f5a_end_rewards_reverts_occurred))))
(define-fun report_effects () Bool (and c103a8f5a_pair_created_with_salt_included
     c103a8f5a_pairfor_inputs_token0_token1_hash
     (not (and c103a8f5a_end_rewards_completes
               (not c103a8f5a_end_rewards_reverts_occurred)))))
(assert report_preconditions)
(check-sat)
(get-model)
