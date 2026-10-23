; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb00d0df2_deposit_permitted () Bool)
(declare-fun cb00d0df2_real_hype_amount () Int)
(declare-fun cb00d0df2_staking_limit () Int)
(declare-fun cb00d0df2_total_claimed () Int)
(declare-fun cb00d0df2_total_rewards () Int)
(declare-fun cb00d0df2_total_slashed () Int)
(declare-fun cb00d0df2_total_staked () Int)
(assert
 (= cb00d0df2_deposit_permitted cb00d0df2_deposit_permitted))
(assert
 (= cb00d0df2_real_hype_amount cb00d0df2_real_hype_amount))
(assert
 (= cb00d0df2_staking_limit cb00d0df2_staking_limit))
(assert
 (= cb00d0df2_total_claimed cb00d0df2_total_claimed))
(assert
 (= cb00d0df2_total_rewards cb00d0df2_total_rewards))
(assert
 (= cb00d0df2_total_slashed cb00d0df2_total_slashed))
(assert
 (= cb00d0df2_total_staked cb00d0df2_total_staked))
(define-fun report_preconditions () Bool (and (= 500 cb00d0df2_staking_limit)
     (= 400 cb00d0df2_total_staked)
     (= 100 cb00d0df2_total_claimed)
     (= 200 cb00d0df2_total_rewards)
     (= 50 cb00d0df2_total_slashed)))
(define-fun report_safety () Bool (=> (= cb00d0df2_real_hype_amount
       (- (+ cb00d0df2_total_staked cb00d0df2_total_rewards)
          (+ cb00d0df2_total_claimed cb00d0df2_total_slashed)))
    (=> (and (< cb00d0df2_real_hype_amount cb00d0df2_staking_limit)
             (= 450 cb00d0df2_real_hype_amount))
        cb00d0df2_deposit_permitted)))
(define-fun report_effects () Bool (and (= cb00d0df2_real_hype_amount
        (- (+ cb00d0df2_total_staked cb00d0df2_total_rewards)
           (+ cb00d0df2_total_claimed cb00d0df2_total_slashed)))
     (< cb00d0df2_real_hype_amount cb00d0df2_staking_limit)
     (= 450 cb00d0df2_real_hype_amount)
     (not cb00d0df2_deposit_permitted)))
