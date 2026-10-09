; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun snapshot_weight () Int)
(declare-fun full_weight () Int)
(declare-fun held_duration () Int)
(declare-fun epoch_duration () Int)
(declare-fun snapshot_defined () Bool)
(declare-fun ratio_duration_blind () Bool)
(assert
 (= snapshot_weight snapshot_weight))
(assert
 (= full_weight full_weight))
(assert
 (= held_duration held_duration))
(assert
 (= epoch_duration epoch_duration))
(assert
 (= snapshot_defined snapshot_defined))
(assert
 (= ratio_duration_blind ratio_duration_blind))
(define-fun report_preconditions () Bool (and snapshot_defined ratio_duration_blind (< 0 epoch_duration)))
(define-fun report_safety () Bool (=> (and snapshot_defined ratio_duration_blind)
    (<= (* snapshot_weight epoch_duration) (* full_weight held_duration))))
(define-fun report_effects () Bool (and snapshot_defined
     ratio_duration_blind
     (not (<= (* snapshot_weight epoch_duration) (* full_weight held_duration)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
