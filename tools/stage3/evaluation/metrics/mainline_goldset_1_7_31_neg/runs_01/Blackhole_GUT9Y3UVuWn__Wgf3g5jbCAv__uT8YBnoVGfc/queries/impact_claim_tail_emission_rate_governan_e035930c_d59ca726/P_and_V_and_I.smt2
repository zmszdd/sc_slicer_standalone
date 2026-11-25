; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c54e3cc30_governor_calls_nudge () Bool)
(declare-fun c54e3cc30_initializer_value () ReportAddress)
(declare-fun c54e3cc30_nudge_reverts () Bool)
(declare-fun c54e3cc30_tail_start () Int)
(declare-fun c54e3cc30_weekly_initialized () Int)
(declare-fun c54e3cc30_zero_address () ReportAddress)
(assert
 (= c54e3cc30_governor_calls_nudge c54e3cc30_governor_calls_nudge))
(assert
 (= c54e3cc30_initializer_value c54e3cc30_initializer_value))
(assert
 (= c54e3cc30_nudge_reverts c54e3cc30_nudge_reverts))
(assert
 (= c54e3cc30_tail_start c54e3cc30_tail_start))
(assert
 (= c54e3cc30_weekly_initialized c54e3cc30_weekly_initialized))
(assert
 (= c54e3cc30_zero_address c54e3cc30_zero_address))
(define-fun report_preconditions () Bool (and (> c54e3cc30_weekly_initialized c54e3cc30_tail_start)
     (distinct c54e3cc30_initializer_value c54e3cc30_zero_address)
     c54e3cc30_governor_calls_nudge))
(define-fun report_safety () Bool (not c54e3cc30_nudge_reverts))
(define-fun report_effects () Bool (and c54e3cc30_governor_calls_nudge
     c54e3cc30_nudge_reverts
     c54e3cc30_nudge_reverts))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
