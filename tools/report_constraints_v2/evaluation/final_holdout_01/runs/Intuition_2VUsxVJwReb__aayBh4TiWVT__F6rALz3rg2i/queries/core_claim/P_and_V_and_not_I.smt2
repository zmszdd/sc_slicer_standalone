; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun epoch_boundary_aligned () Bool)
(declare-fun claim_previous_epoch () Bool)
(declare-fun deposit_before_epoch_end () Bool)
(declare-fun attacker_reward_share () Int)
(declare-fun honest_continuous_share () Int)
(assert
 (= epoch_boundary_aligned epoch_boundary_aligned))
(assert
 (= claim_previous_epoch claim_previous_epoch))
(assert
 (= deposit_before_epoch_end deposit_before_epoch_end))
(assert
 (= attacker_reward_share attacker_reward_share))
(assert
 (= honest_continuous_share honest_continuous_share))
(define-fun report_preconditions () Bool (and epoch_boundary_aligned claim_previous_epoch deposit_before_epoch_end))
(define-fun report_safety () Bool (=> (and epoch_boundary_aligned claim_previous_epoch deposit_before_epoch_end)
    (<= attacker_reward_share honest_continuous_share)))
(define-fun report_effects () Bool (and epoch_boundary_aligned
     claim_previous_epoch
     deposit_before_epoch_end
     (not (<= attacker_reward_share honest_continuous_share))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
