; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3ad43646_emission_indexed () Bool)
(declare-fun c3ad43646_reward_pool_shrunk () Bool)
(declare-fun c3ad43646_total_weight () Int)
(assert
 (= c3ad43646_emission_indexed c3ad43646_emission_indexed))
(assert
 (= c3ad43646_reward_pool_shrunk c3ad43646_reward_pool_shrunk))
(assert
 (= c3ad43646_total_weight c3ad43646_total_weight))
(define-fun report_preconditions () Bool (= 0 c3ad43646_total_weight))
(define-fun report_safety () Bool (=> (= 0 c3ad43646_total_weight)
    (and c3ad43646_emission_indexed (not c3ad43646_reward_pool_shrunk))))
(define-fun report_effects () Bool (and (= 0 c3ad43646_total_weight)
     (not (and c3ad43646_emission_indexed (not c3ad43646_reward_pool_shrunk)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
