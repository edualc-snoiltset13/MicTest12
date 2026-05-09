package com.abc_bank.abc_bank.notification.repo;

import com.abc_bank.abc_bank.notification.entity.Notification;
import org.springframework.data.jpa.repository.JpaRepository;

public interface NotificationRepo extends JpaRepository<Notification,Long> {
}
