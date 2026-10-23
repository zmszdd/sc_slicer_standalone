; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ceee3c1d7_block_timestamp_exceeds_deadline () Bool)
(declare-fun ceee3c1d7_caller_is_owner () Bool)
(declare-fun ceee3c1d7_deadline_is_caller_provided () Bool)
(declare-fun ceee3c1d7_mev_bot_extracts_value () Bool)
(declare-fun ceee3c1d7_mev_bot_monitors_mempool () Bool)
(declare-fun ceee3c1d7_transaction_rejected_after_expiry () Bool)
(assert
 (= ceee3c1d7_block_timestamp_exceeds_deadline ceee3c1d7_block_timestamp_exceeds_deadline))
(assert
 (= ceee3c1d7_caller_is_owner ceee3c1d7_caller_is_owner))
(assert
 (= ceee3c1d7_deadline_is_caller_provided ceee3c1d7_deadline_is_caller_provided))
(assert
 (= ceee3c1d7_mev_bot_extracts_value ceee3c1d7_mev_bot_extracts_value))
(assert
 (= ceee3c1d7_mev_bot_monitors_mempool ceee3c1d7_mev_bot_monitors_mempool))
(assert
 (= ceee3c1d7_transaction_rejected_after_expiry ceee3c1d7_transaction_rejected_after_expiry))
(define-fun report_preconditions () Bool (and ceee3c1d7_caller_is_owner ceee3c1d7_mev_bot_monitors_mempool))
(define-fun report_safety () Bool (=> (and ceee3c1d7_deadline_is_caller_provided
         ceee3c1d7_block_timestamp_exceeds_deadline)
    (and ceee3c1d7_transaction_rejected_after_expiry
         (not ceee3c1d7_mev_bot_extracts_value))))
(define-fun report_effects () Bool (and ceee3c1d7_deadline_is_caller_provided
     ceee3c1d7_block_timestamp_exceeds_deadline
     (not (and ceee3c1d7_transaction_rejected_after_expiry
               (not ceee3c1d7_mev_bot_extracts_value)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
