; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun duration_seconds () Int)
(declare-fun epoch_duration_seconds () Int)
(declare-fun campaign_covers_partial_epoch () Bool)
(assert
 (= duration_seconds duration_seconds))
(assert
 (= epoch_duration_seconds epoch_duration_seconds))
(assert
 (= campaign_covers_partial_epoch campaign_covers_partial_epoch))
(define-fun report_preconditions () Bool (distinct 0 (mod duration_seconds 3600)))
(define-fun report_safety () Bool (=> (distinct 0 (mod duration_seconds 3600))
    (not campaign_covers_partial_epoch)))
(define-fun report_effects () Bool (and (distinct 0 (mod duration_seconds 3600)) campaign_covers_partial_epoch))
