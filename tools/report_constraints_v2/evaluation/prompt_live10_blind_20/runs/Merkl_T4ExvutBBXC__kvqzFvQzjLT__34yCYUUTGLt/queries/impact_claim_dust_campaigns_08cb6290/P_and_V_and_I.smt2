; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3b2fc460_dust_campaign_created () Bool)
(declare-fun c3b2fc460_gross_amount () Int)
(declare-fun c3b2fc460_minimum_reward_threshold () Int)
(declare-fun c3b2fc460_net_real_amount () Int)
(assert
 (= c3b2fc460_dust_campaign_created c3b2fc460_dust_campaign_created))
(assert
 (= c3b2fc460_gross_amount c3b2fc460_gross_amount))
(assert
 (= c3b2fc460_minimum_reward_threshold c3b2fc460_minimum_reward_threshold))
(assert
 (= c3b2fc460_net_real_amount c3b2fc460_net_real_amount))
(define-fun report_preconditions () Bool (and (< c3b2fc460_net_real_amount c3b2fc460_gross_amount)
     (> c3b2fc460_gross_amount c3b2fc460_minimum_reward_threshold)))
(define-fun report_safety () Bool (=> (and (> c3b2fc460_gross_amount c3b2fc460_minimum_reward_threshold)
         (< c3b2fc460_net_real_amount c3b2fc460_gross_amount))
    (and (>= c3b2fc460_net_real_amount c3b2fc460_minimum_reward_threshold)
         (not c3b2fc460_dust_campaign_created))))
(define-fun report_effects () Bool (and (> c3b2fc460_gross_amount c3b2fc460_minimum_reward_threshold)
     (< c3b2fc460_net_real_amount c3b2fc460_gross_amount)
     (not (and (>= c3b2fc460_net_real_amount c3b2fc460_minimum_reward_threshold)
               (not c3b2fc460_dust_campaign_created)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
