; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c12313a3e_attacker_quote_supplied_wei () Int)
(declare-fun c12313a3e_graduation_succeeds () Bool)
(declare-fun c12313a3e_pair_deployed_before_graduation () Bool)
(declare-fun c12313a3e_pair_token_a_reserve_wei () Int)
(declare-fun c12313a3e_token_near_graduation () Bool)
(assert
 (= c12313a3e_attacker_quote_supplied_wei c12313a3e_attacker_quote_supplied_wei))
(assert
 (= c12313a3e_graduation_succeeds c12313a3e_graduation_succeeds))
(assert
 (= c12313a3e_pair_deployed_before_graduation c12313a3e_pair_deployed_before_graduation))
(assert
 (= c12313a3e_pair_token_a_reserve_wei c12313a3e_pair_token_a_reserve_wei))
(assert
 (= c12313a3e_token_near_graduation c12313a3e_token_near_graduation))
(define-fun report_preconditions () Bool (and c12313a3e_token_near_graduation
     c12313a3e_pair_deployed_before_graduation
     (= 1 c12313a3e_pair_token_a_reserve_wei)))
(define-fun report_safety () Bool (=> (and c12313a3e_token_near_graduation
         c12313a3e_pair_deployed_before_graduation
         (= 1 c12313a3e_pair_token_a_reserve_wei)
         (= 1 c12313a3e_attacker_quote_supplied_wei))
    c12313a3e_graduation_succeeds))
(define-fun report_effects () Bool (and c12313a3e_token_near_graduation
     c12313a3e_pair_deployed_before_graduation
     (= 1 c12313a3e_pair_token_a_reserve_wei)
     (= 1 c12313a3e_attacker_quote_supplied_wei)
     (not c12313a3e_graduation_succeeds)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
