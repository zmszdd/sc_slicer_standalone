; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9ce3b628_graduation_completes () Bool)
(declare-fun c9ce3b628_launch_token_near_bonding_supply () Bool)
(declare-fun c9ce3b628_pair_deployed_before_graduation () Bool)
(declare-fun c9ce3b628_tokens_movable_into_pair () Bool)
(assert
 (= c9ce3b628_graduation_completes c9ce3b628_graduation_completes))
(assert
 (= c9ce3b628_launch_token_near_bonding_supply c9ce3b628_launch_token_near_bonding_supply))
(assert
 (= c9ce3b628_pair_deployed_before_graduation c9ce3b628_pair_deployed_before_graduation))
(assert
 (= c9ce3b628_tokens_movable_into_pair c9ce3b628_tokens_movable_into_pair))
(define-fun report_preconditions () Bool (and c9ce3b628_launch_token_near_bonding_supply
     c9ce3b628_pair_deployed_before_graduation))
(define-fun report_safety () Bool (=> (and c9ce3b628_launch_token_near_bonding_supply
         c9ce3b628_pair_deployed_before_graduation)
    (or c9ce3b628_graduation_completes c9ce3b628_tokens_movable_into_pair)))
(define-fun report_effects () Bool (and c9ce3b628_launch_token_near_bonding_supply
     c9ce3b628_pair_deployed_before_graduation
     (not (or c9ce3b628_graduation_completes c9ce3b628_tokens_movable_into_pair))))
